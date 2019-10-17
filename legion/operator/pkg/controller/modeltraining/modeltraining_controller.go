//
//    Copyright 2019 EPAM Systems
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.
//

package modeltraining

import (
	"context"
	"fmt"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	train_conf "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	train_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	train_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training/kubernetes"
	"github.com/spf13/viper"
	tektonv1alpha1 "github.com/tektoncd/pipeline/pkg/apis/pipeline/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

const (
	controllerName   = "modeltraining_controller"
	evictedPodReason = "Evicted"
)

var log = logf.Log.WithName(controllerName)

// Add creates a new ModelTraining Controller and adds it to the Manager with default RBAC.
// The Manager will set fields on the Controller and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	k8sClient := mgr.GetClient()

	return &ReconcileModelTraining{
		Client:   k8sClient,
		config:   mgr.GetConfig(),
		scheme:   mgr.GetScheme(),
		recorder: mgr.GetRecorder(controllerName),
		trainRepo: train_k8s_repository.NewRepository(
			viper.GetString(train_conf.Namespace),
			viper.GetString(train_conf.ToolchainIntegrationNamespace),
			k8sClient,
			mgr.GetConfig(),
		),
	}
}

// add adds a new Controller to mgr with r as the reconcile.Reconciler
func add(mgr manager.Manager, r reconcile.Reconciler) error {
	// Create a new controller
	c, err := controller.New("modeltraining-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		log.Error(err, "Cannot create Controller")
		return err
	}

	// Watch for changes to ModelTraining
	if err := c.Watch(&source.Kind{Type: &legionv1alpha1.ModelTraining{}},
		&handler.EnqueueRequestForObject{}); err != nil {
		log.Error(err, "Cannot create watch for ModelTraining CR instances")
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Pod{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelTraining{},
	})
	if err != nil {
		log.Error(err, "Cannot create watch for ModelTraining CR children training Pod")
		return err
	}

	err = c.Watch(&source.Kind{Type: &tektonv1alpha1.TaskRun{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelTraining{},
	})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelTraining{}

// ReconcileModelTraining reconciles a ModelTraining object
type ReconcileModelTraining struct {
	client.Client
	scheme    *runtime.Scheme
	recorder  record.EventRecorder
	config    *rest.Config
	trainRepo train_repository.Repository
}

type BuilderConf struct {
	Builder struct {
		SSHKeyPath string `json:"ssh_key_path"`
	} `json:"trainer"`
}

const (
	mtConfig = "mt.json"
)

var (
	trainerResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
	}
)

// Determine crd state by child pod.
// If pod has RUNNING state then we determine crd state by state of trainer container in the pod
func (r *ReconcileModelTraining) syncCrdState(
	taskRun *tektonv1alpha1.TaskRun,
	trainingCR *legionv1alpha1.ModelTraining,
) error {
	if len(taskRun.Status.Conditions) > 0 {
		if err := r.calculateStateByTaskRun(taskRun, trainingCR); err != nil {
			return err
		}
	} else {
		trainingCR.Status.State = legionv1alpha1.ModelTrainingScheduling
	}

	log.Info("Setup training state", "mt_id", trainingCR.Name, "state", trainingCR.Status.State)

	trainingCR.Status.PodName = taskRun.Status.PodName

	return r.Update(context.TODO(), trainingCR)
}

func (r *ReconcileModelTraining) calculateStateByTaskRun(
	taskRun *tektonv1alpha1.TaskRun,
	trainingCR *legionv1alpha1.ModelTraining,
) error {
	lastCondition := taskRun.Status.Conditions[len(taskRun.Status.Conditions)-1]

	switch lastCondition.Status {
	case corev1.ConditionUnknown:
		if len(taskRun.Status.PodName) != 0 {
			if err := r.calculateStateByPod(taskRun.Status.PodName, trainingCR); err != nil {
				return err
			}
		} else {
			trainingCR.Status.State = legionv1alpha1.ModelTrainingScheduling
		}
	case corev1.ConditionTrue:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingSucceeded
		trainingCR.Status.Message = &lastCondition.Message
		trainingCR.Status.Reason = &lastCondition.Reason

		result, err := r.trainRepo.GetModelTrainingResult(trainingCR.Name)
		if err != nil {
			return err
		}

		trainingCR.Status.Artifacts = append(trainingCR.Status.Artifacts, *result)
	case corev1.ConditionFalse:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingFailed
		trainingCR.Status.Message = &lastCondition.Message
		trainingCR.Status.Reason = &lastCondition.Reason
	default:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingScheduling
	}
	return nil
}

// When tekton task run has the unknown state, we calculate CRD state by pod
func (r *ReconcileModelTraining) calculateStateByPod(
	trainerPodName string, trainingCR *legionv1alpha1.ModelTraining) error {
	trainerPod := &corev1.Pod{}
	if err := r.Get(
		context.TODO(),
		types.NamespacedName{
			Name:      trainerPodName,
			Namespace: trainingCR.Namespace,
		},
		trainerPod,
	); err != nil {
		return err
	}

	if trainerPod.Status.Reason == evictedPodReason {
		trainingCR.Status.State = legionv1alpha1.ModelTrainingFailed
		trainingCR.Status.Message = &trainerPod.Status.Message

		return nil
	}

	switch trainerPod.Status.Phase {
	case corev1.PodPending:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingScheduling
	case corev1.PodUnknown:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingScheduling
	case corev1.PodRunning:
		trainingCR.Status.State = legionv1alpha1.ModelTrainingRunning
	}

	return nil
}

func (r *ReconcileModelTraining) getToolchainIntegration(trainingCR *legionv1alpha1.ModelTraining) (
	*training.ToolchainIntegration, error,
) {
	var ti legionv1alpha1.ToolchainIntegration
	if err := r.Get(context.TODO(), types.NamespacedName{
		Name:      trainingCR.Spec.Toolchain,
		Namespace: viper.GetString(train_conf.ToolchainIntegrationNamespace),
	}, &ti); err != nil {
		log.Error(err, "Get toolchain integration", "mt id", trainingCR)
		return nil, err
	}
	return &training.ToolchainIntegration{Spec: ti.Spec}, nil
}

func (r *ReconcileModelTraining) reconcileTaskRun(
	trainingCR *legionv1alpha1.ModelTraining,
) (*tektonv1alpha1.TaskRun, error) {
	if trainingCR.Status.State != "" && trainingCR.Status.State != legionv1alpha1.ModelTrainingUnknown {
		taskRun := &tektonv1alpha1.TaskRun{}
		err := r.Get(context.TODO(), types.NamespacedName{
			Name: trainingCR.Name, Namespace: viper.GetString(train_conf.Namespace),
		}, taskRun)
		if err != nil {
			return nil, err
		}

		log.Info("Training has no unknown state. Skip the task run reconcile",
			"mt id", trainingCR.Name, "state", trainingCR.Status.State)
		return taskRun, nil
	}

	toolchainIntegration, err := r.getToolchainIntegration(trainingCR)
	if err != nil {
		return nil, err
	}

	tolerations := []corev1.Toleration{}
	tolerationConf := viper.GetStringMapString(train_conf.Toleration)
	if len(tolerationConf) != 0 {
		tolerations = append(tolerations, corev1.Toleration{
			Key:      tolerationConf[train_conf.TolerationKey],
			Operator: corev1.TolerationOperator(tolerationConf[train_conf.TolerationOperator]),
			Value:    tolerationConf[train_conf.TolerationValue],
			Effect:   corev1.TaintEffect(tolerationConf[train_conf.TolerationEffect]),
		})
	}

	taskSpec, err := generateTrainerTaskSpec(trainingCR, toolchainIntegration)
	if err != nil {
		return nil, err
	}

	taskRun := &tektonv1alpha1.TaskRun{
		ObjectMeta: metav1.ObjectMeta{
			Name:      trainingCR.Name,
			Namespace: trainingCR.Namespace,
		},
		Spec: tektonv1alpha1.TaskRunSpec{
			TaskSpec: taskSpec,
			Timeout:  &metav1.Duration{Duration: viper.GetDuration(train_conf.Timeout)},
			PodTemplate: tektonv1alpha1.PodTemplate{
				NodeSelector: viper.GetStringMapString(train_conf.NodeSelector),
				Tolerations:  tolerations,
			},
		},
	}

	if err := controllerutil.SetControllerReference(trainingCR, taskRun, r.scheme); err != nil {
		return nil, err
	}

	if err := legion.StoreHash(taskRun); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return nil, err
	}

	found := &tektonv1alpha1.TaskRun{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: taskRun.Name, Namespace: viper.GetString(train_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s task run", taskRun.ObjectMeta.Name))
		return taskRun, r.Create(context.TODO(), taskRun)
	} else if err != nil {
		return nil, err
	}

	if err := r.Delete(context.TODO(), found); err != nil {
		return nil, err
	}

	return taskRun, r.Create(context.TODO(), taskRun)
}

func (r *ReconcileModelTraining) createResultConfigMap(trainingCR *legionv1alpha1.ModelTraining) error {
	resultCM := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      legion.GenerateTrainingResultCMName(trainingCR.Name),
			Namespace: viper.GetString(train_conf.Namespace),
		},
		Data: map[string]string{},
	}

	if err := controllerutil.SetControllerReference(trainingCR, resultCM, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(resultCM); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.ConfigMap{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: resultCM.Name, Namespace: viper.GetString(train_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s result config map", resultCM.ObjectMeta.Name))
		err = r.Create(context.TODO(), resultCM)
		return err
	}

	return err
}

func isTrainingFinished(mt *legionv1alpha1.ModelTraining) bool {
	state := mt.Status.State

	return state == legionv1alpha1.ModelTrainingSucceeded || state == legionv1alpha1.ModelTrainingFailed
}

// Reconcile reads that state of the cluster for a ModelTraining object and makes changes based on the state read
// and what is in the ModelTraining.Spec
// +kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=pods/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=pods/exec,verbs=create
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=toolchainintegrations,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=toolchainintegrations/status,verbs=get;update;patch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelTraining) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	trainingCR := &legionv1alpha1.ModelTraining{}

	if err := r.Get(context.TODO(), request.NamespacedName, trainingCR); err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}
		log.Error(err, "Cannot fetch CR status")
		return reconcile.Result{}, err
	}

	if isTrainingFinished(trainingCR) {
		log.Info("Training has been finished. Skip reconcile function", "mt id", trainingCR.Name)

		return reconcile.Result{}, nil
	}

	// The configmap is used to save a training result.
	if err := r.createResultConfigMap(trainingCR); err != nil {
		log.Error(err, "Can not create result config map")

		return reconcile.Result{}, err
	}

	if taskRun, err := r.reconcileTaskRun(trainingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S instances state to cluster")

		return reconcile.Result{}, err
	} else if err := r.syncCrdState(taskRun, trainingCR); err != nil {
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
