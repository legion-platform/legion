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

package modelpackaging

import (
	"context"
	"fmt"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packaging_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	packaging_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	packaging_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	"github.com/spf13/viper"
	tektonv1alpha1 "github.com/tektoncd/pipeline/pkg/apis/pipeline/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

var log = logf.Log.WithName("model-packager-controller")

// Add creates a new ModelPackaging Controller and adds it to the Manager with default RBAC.
// The Manager will set fields on the Controller and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	k8sClient := mgr.GetClient()

	return &ReconcileModelPackaging{
		Client: k8sClient,
		scheme: mgr.GetScheme(),
		config: mgr.GetConfig(),
		packRepo: packaging_k8s_repository.NewRepository(
			viper.GetString(packaging_conf.Namespace),
			viper.GetString(packaging_conf.PackagingIntegrationNamespace),
			k8sClient,
			mgr.GetConfig(),
		),
	}
}

// add adds a new Controller to mgr with r as the reconcile.Reconciler
func add(mgr manager.Manager, r reconcile.Reconciler) error {
	// Create a new controller
	c, err := controller.New("modelpackaging-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	// Watch for changes to ModelPackaging
	err = c.Watch(&source.Kind{Type: &legionv1alpha1.ModelPackaging{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Pod{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelPackaging{},
	})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &tektonv1alpha1.TaskRun{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelPackaging{},
	})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelPackaging{}

// ReconcileModelPackaging reconciles a ModelPackaging object
type ReconcileModelPackaging struct {
	client.Client
	scheme   *runtime.Scheme
	config   *rest.Config
	packRepo packaging_repository.Repository
}

const (
	mpContentFile    = "mp.json"
	evictedPodReason = "Evicted"
)

var (
	packagerResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	packagingPrivileged = true
)

// Determine crd state by child pod.
// If pod has RUNNING state then we determine crd state by state of packager container in the pod
func (r *ReconcileModelPackaging) syncCrdState(
	taskRun *tektonv1alpha1.TaskRun,
	packagingCR *legionv1alpha1.ModelPackaging,
) error {
	if len(taskRun.Status.Conditions) > 0 {
		if err := r.calculateStateByTaskRun(taskRun, packagingCR); err != nil {
			return err
		}
	} else {
		packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
	}

	log.Info("Setup packaging state", "mp_id", packagingCR.Name, "state", packagingCR.Status.State)

	packagingCR.Status.PodName = taskRun.Status.PodName

	return r.Update(context.TODO(), packagingCR)
}

func (r *ReconcileModelPackaging) calculateStateByTaskRun(
	taskRun *tektonv1alpha1.TaskRun,
	packagingCR *legionv1alpha1.ModelPackaging,
) error {
	lastCondition := taskRun.Status.Conditions[len(taskRun.Status.Conditions)-1]

	switch lastCondition.Status {
	case corev1.ConditionUnknown:
		if len(taskRun.Status.PodName) != 0 {
			if err := r.calculateStateByPod(taskRun.Status.PodName, packagingCR); err != nil {
				return err
			}
		} else {
			packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
		}
	case corev1.ConditionTrue:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingSucceeded
		packagingCR.Status.Message = &lastCondition.Message
		packagingCR.Status.Reason = &lastCondition.Reason

		results, err := r.packRepo.GetModelPackagingResult(packagingCR.Name)
		if err != nil {
			return err
		}

		packagingCR.Status.Results = results
	case corev1.ConditionFalse:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingFailed
		packagingCR.Status.Message = &lastCondition.Message
		packagingCR.Status.Reason = &lastCondition.Reason
	default:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
	}
	return nil
}

// When tekton task run has the unknown state, we calculate CRD state by pod
func (r *ReconcileModelPackaging) calculateStateByPod(
	packagerPodName string, packagingCR *legionv1alpha1.ModelPackaging) error {
	packagerPod := &corev1.Pod{}
	if err := r.Get(
		context.TODO(),
		types.NamespacedName{
			Name:      packagerPodName,
			Namespace: packagingCR.Namespace,
		},
		packagerPod,
	); err != nil {
		return err
	}

	if packagerPod.Status.Reason == evictedPodReason {
		packagingCR.Status.State = legionv1alpha1.ModelPackagingFailed
		packagingCR.Status.Message = &packagerPod.Status.Message

		return nil
	}

	switch packagerPod.Status.Phase {
	case corev1.PodPending:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
	case corev1.PodUnknown:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
	case corev1.PodRunning:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingRunning
	}

	return nil
}

func (r *ReconcileModelPackaging) getPackagingIntegration(packagingCR *legionv1alpha1.ModelPackaging) (
	*packaging.PackagingIntegration, error,
) {
	var ti legionv1alpha1.PackagingIntegration
	if err := r.Get(context.TODO(), types.NamespacedName{
		Name:      packagingCR.Spec.Type,
		Namespace: viper.GetString(packaging_conf.PackagingIntegrationNamespace),
	}, &ti); err != nil {
		log.Error(err, "Get toolchain integration", "mt name", packagingCR)
		return nil, err
	}
	return mp_k8s_repository.TransformPackagingIntegrationFromK8s(&ti)
}

func (r *ReconcileModelPackaging) reconcileTaskRun(
	packagingCR *legionv1alpha1.ModelPackaging,
) (*tektonv1alpha1.TaskRun, error) {
	if packagingCR.Status.State != "" && packagingCR.Status.State != legionv1alpha1.ModelPackagingUnknown {
		taskRun := &tektonv1alpha1.TaskRun{}
		err := r.Get(context.TODO(), types.NamespacedName{
			Name: packagingCR.Name, Namespace: viper.GetString(packaging_conf.Namespace),
		}, taskRun)
		if err != nil {
			return nil, err
		}

		log.Info("Packaging has no unknown state. Skip the task run reconcile",
			"mt id", packagingCR.Name, "state", packagingCR.Status.State)
		return taskRun, nil
	}

	packagingIntegration, err := r.getPackagingIntegration(packagingCR)
	if err != nil {
		return nil, err
	}

	tolerations := []corev1.Toleration{}
	tolerationConf := viper.GetStringMapString(packaging_conf.Toleration)
	if len(tolerationConf) != 0 {
		tolerations = append(tolerations, corev1.Toleration{
			Key:      tolerationConf[packaging_conf.TolerationKey],
			Operator: corev1.TolerationOperator(tolerationConf[packaging_conf.TolerationOperator]),
			Value:    tolerationConf[packaging_conf.TolerationValue],
			Effect:   corev1.TaintEffect(tolerationConf[packaging_conf.TolerationEffect]),
		})
	}

	taskSpec, err := generatePackagerTaskSpec(packagingCR, packagingIntegration)
	if err != nil {
		return nil, err
	}

	taskRun := &tektonv1alpha1.TaskRun{
		ObjectMeta: metav1.ObjectMeta{
			Name:      packagingCR.Name,
			Namespace: packagingCR.Namespace,
		},
		Spec: tektonv1alpha1.TaskRunSpec{
			TaskSpec: taskSpec,
			Timeout:  &metav1.Duration{Duration: viper.GetDuration(packaging_conf.Timeout)},
			PodTemplate: tektonv1alpha1.PodTemplate{
				NodeSelector: viper.GetStringMapString(packaging_conf.NodeSelector),
				Tolerations:  tolerations,
			},
		},
	}

	if err := controllerutil.SetControllerReference(packagingCR, taskRun, r.scheme); err != nil {
		return nil, err
	}

	if err := legion.StoreHash(taskRun); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return nil, err
	}

	found := &tektonv1alpha1.TaskRun{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: taskRun.Name, Namespace: viper.GetString(packaging_conf.Namespace),
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

func (r *ReconcileModelPackaging) createResultConfigMap(packagingCR *legionv1alpha1.ModelPackaging) error {
	resultCM := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      legion.GeneratePackageResultCMName(packagingCR.Name),
			Namespace: viper.GetString(packaging_conf.Namespace),
		},
		Data: map[string]string{},
	}

	if err := controllerutil.SetControllerReference(packagingCR, resultCM, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(resultCM); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.ConfigMap{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: resultCM.Name, Namespace: viper.GetString(packaging_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s result config map", resultCM.ObjectMeta.Name))
		err = r.Create(context.TODO(), resultCM)
		return err
	}

	return err
}

func isPackagingFinished(mp *legionv1alpha1.ModelPackaging) bool {
	state := mp.Status.State

	return state == legionv1alpha1.ModelPackagingSucceeded || state == legionv1alpha1.ModelPackagingFailed
}

// Reconcile reads that state of the cluster for a ModelPackaging object and makes changes based on the state read
// and what is in the ModelPackaging.Spec
// +kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=pods/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=,resources=configmaps,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=,resources=configmaps/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=pods/exec,verbs=create
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=packagingintegrations,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=packagingintegrations/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=tekton.dev,resources=taskruns,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=tekton.dev,resources=taskruns/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=connecitons,verbs=get;list
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelPackaging) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ModelPackaging
	packagingCR := &legionv1alpha1.ModelPackaging{}

	if err := r.Get(context.TODO(), request.NamespacedName, packagingCR); err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}
		log.Error(err, "Cannot fetch CR status")
		return reconcile.Result{}, err
	}

	if isPackagingFinished(packagingCR) {
		log.Info("Packaging has been finished. Skip reconcile function", "mp name", packagingCR.Name)

		return reconcile.Result{}, nil
	}

	// The configmap is used to save a packaging result.
	if err := r.createResultConfigMap(packagingCR); err != nil {
		log.Error(err, "Can not create result config map")

		return reconcile.Result{}, err
	}

	if taskRun, err := r.reconcileTaskRun(packagingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S instances state to cluster")

		return reconcile.Result{}, err
	} else if err := r.syncCrdState(taskRun, packagingCR); err != nil {
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
