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
	"encoding/json"
	std_errors "errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/trainer"
	"github.com/spf13/viper"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/record"
	"path"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	conn_conf "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	train_conf "github.com/legion-platform/legion/legion/operator/pkg/config/training"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

const (
	controllerName = "modeltraining_controller"
)

var log = logf.Log.WithName(controllerName)

// Add creates a new ModelTraining Controller and adds it to the Manager with default RBAC.
// The Manager will set fields on the Controller and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return &ReconcileModelTraining{
		Client:   mgr.GetClient(),
		config:   mgr.GetConfig(),
		scheme:   mgr.GetScheme(),
		recorder: mgr.GetRecorder(controllerName),
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

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelTraining{}

var (
	secretDefaultMode             = int32(420)
	terminationGracePeriodSeconds = int64(0)
	trainingPrivileged            = true
)

// ReconcileModelTraining reconciles a ModelTraining object
type ReconcileModelTraining struct {
	client.Client
	scheme   *runtime.Scheme
	recorder record.EventRecorder
	config   *rest.Config
}

type BuilderConf struct {
	Builder struct {
		SSHKeyPath string `json:"ssh_key_path"`
	} `json:"trainer"`
}

const (
	gitSecretVolumeName = "git-secrets"
	gitSecretPath       = "/home/root/.ssh" //nolint
	gitSSHVolumeName    = "git-ssh"
	gitSSHVolumePath    = "/etc/ssh"
	containerName       = "trainer"
	configVolume        = "config"
	TrainStartCommand   = "/opt/legion/trainer"
	TrainConfigPath     = "/etc/legion/trainer.conf.yaml"
	MtConfig            = "/etc/legion/mt.json"
	configDir           = "/etc/legion"
	evictedPodReason    = "Evicted"
)

// Determine crd state by child pod.
// If pod has RUNNING state then we determine crd state by state of trainer container in the pod
func (r *ReconcileModelTraining) syncCrdState(pod *corev1.Pod, trainCrd *legionv1alpha1.ModelTraining) error {
	switch pod.Status.Phase {
	case corev1.PodPending:
		trainCrd.Status.State = legionv1alpha1.ModelTrainingScheduling
	case corev1.PodRunning:
		trainCrd.Status.State = legionv1alpha1.ModelTrainingRunning
	case corev1.PodSucceeded:
		if len(pod.Status.ContainerStatuses) != 1 {
			err := std_errors.New("impossible situation. Training pod must contain only one container")
			log.Error(err, "mt name", trainCrd.Name)
			return err
		}

		container := pod.Status.ContainerStatuses[0]
		if container.State.Terminated == nil {
			err := std_errors.New("impossible situation. Training container must be terminated")
			log.Error(err, "mt name", trainCrd.Name)
			return err
		}

		if container.State.Terminated.ExitCode != 0 {
			err := fmt.Errorf(
				"impossible situation. Pod is succeeded, but container exit code is %d",
				container.State.Terminated.ExitCode,
			)
			log.Error(err, "mt name", trainCrd.Name)
			return err
		}

		trainCrd.Status.State = legionv1alpha1.ModelTrainingSucceeded

		outputZipName := pod.Annotations[legion.TrainingOutputZip]
		trainingRunID := pod.Annotations[legion.TrainingRunID]
		commitID := pod.Annotations[legion.ModelCommitID]

		if trainCrd.ObjectMeta.Labels == nil {
			trainCrd.ObjectMeta.Labels = map[string]string{}
		}

		if len(trainCrd.Status.Artifacts) == 0 {
			trainCrd.Status.Artifacts = []legionv1alpha1.TrainingResult{}
		}

		trainCrd.Status.Artifacts = append(trainCrd.Status.Artifacts, legionv1alpha1.TrainingResult{
			RunID:        trainingRunID,
			ArtifactName: outputZipName,
			CommitID:     commitID,
		})
	case corev1.PodFailed:
		trainCrd.Status.State = legionv1alpha1.ModelTrainingFailed

		if pod.Status.Reason == evictedPodReason {
			trainCrd.Status.Message = &pod.Status.Message

			return nil
		}

		if len(pod.Status.ContainerStatuses) != 1 {
			err := std_errors.New("impossible situation. Training pod must contain only one container")
			log.Error(err, "mt name", trainCrd.Name)
			return err
		}

		container := pod.Status.ContainerStatuses[0]
		if container.State.Terminated == nil {
			err := std_errors.New("impossible situation. Training container must be terminated")
			log.Error(err, "mt name", trainCrd.Name)
			return err
		}

		trainCrd.Status.Message = &container.State.Terminated.Message
		trainCrd.Status.ExitCode = &container.State.Terminated.ExitCode
		trainCrd.Status.Reason = &container.State.Terminated.Reason
	case corev1.PodUnknown:
		trainCrd.Status.State = legionv1alpha1.ModelTrainingUnknown
	}

	if err := r.Update(context.TODO(), trainCrd); err != nil {
		return err
	}

	return nil
}

func (r *ReconcileModelTraining) getVcsConnection(trainingCR *legionv1alpha1.ModelTraining) (
	*connection.Connection, error,
) {
	vcsName := trainingCR.Spec.VCSName
	vcs := &legionv1alpha1.Connection{}
	if err := r.Get(context.TODO(), types.NamespacedName{
		Namespace: viper.GetString(conn_conf.Namespace),
		Name:      vcsName,
	}, vcs); err != nil {
		log.Error(err, "Get vcs connection",
			"md id", trainingCR.Name,
			"vcs name", vcs)
		return nil, err
	}
	return &connection.Connection{
		ID:   trainingCR.Spec.VCSName,
		Spec: vcs.Spec,
	}, nil
}

func (r *ReconcileModelTraining) getOutputConnection() (*connection.Connection, error) {
	vcs := &legionv1alpha1.Connection{}
	if err := r.Get(context.TODO(), types.NamespacedName{
		Namespace: viper.GetString(conn_conf.Namespace),
		Name:      viper.GetString(train_conf.OutputConnectionName),
	}, vcs); err != nil {
		log.Error(err, "Get output connection", "vcs name", vcs)
		return nil, err
	}
	return &connection.Connection{
		ID:   viper.GetString(train_conf.OutputConnectionName),
		Spec: vcs.Spec,
	}, nil
}

func (r *ReconcileModelTraining) getToolchainIntegration(trainingCR *legionv1alpha1.ModelTraining) (
	*training.ToolchainIntegration, error,
) {
	var ti legionv1alpha1.ToolchainIntegration
	if err := r.Get(context.TODO(), types.NamespacedName{
		Name:      trainingCR.Spec.Toolchain,
		Namespace: viper.GetString(train_conf.ToolchainIntegrationNamespace),
	}, &ti); err != nil {
		log.Error(err, "Get toolchain integration", "md id", trainingCR)
		return nil, err
	}
	return &training.ToolchainIntegration{Spec: ti.Spec}, nil
}

func (r *ReconcileModelTraining) generateInputData(trainingCR *legionv1alpha1.ModelTraining) (
	[]training.InputDataBindingDir, error,
) {
	inputData := make([]training.InputDataBindingDir, 0, len(trainingCR.Spec.Data))
	for _, trainData := range trainingCR.Spec.Data {
		var trainDataConnSpec legionv1alpha1.ConnectionSpec

		var trainDataConn legionv1alpha1.Connection

		if err := r.Get(context.TODO(), types.NamespacedName{
			Name: trainData.Connection, Namespace: viper.GetString(conn_conf.Namespace),
		}, &trainDataConn); err != nil {

			log.Error(err, "Get train data",
				"mt id", trainingCR.Name,
				"conn id", trainData.Connection)

			return nil, err
		}

		trainDataConnSpec = trainDataConn.Spec

		inputData = append(inputData, training.InputDataBindingDir{
			LocalPath:   trainData.LocalPath,
			RemotePath:  trainData.RemotePath,
			DataBinding: trainDataConnSpec,
		})
	}
	return inputData, nil
}

func (r *ReconcileModelTraining) reconcilePod(trainingCR *legionv1alpha1.ModelTraining) (*corev1.Pod, error) {
	if trainingCR.Status.State != "" && trainingCR.Status.State != legionv1alpha1.ModelTrainingUnknown {
		pod := &corev1.Pod{}
		err := r.Get(context.TODO(), types.NamespacedName{
			Name: trainingCR.Name, Namespace: viper.GetString(train_conf.Namespace),
		}, pod)
		if err != nil {
			return nil, err
		}

		log.Info("Training has no unknown state. Skip the pod reconcile",
			"mt id", trainingCR.Name, "state", trainingCR.Status.State)
		return pod, nil
	}

	mtResources, err := kubernetes.ConvertLegionResourcesToK8s(trainingCR.Spec.Resources)
	if err != nil {
		return nil, err
	}

	var tolerations []corev1.Toleration
	nodeSelector := viper.GetStringMapString(train_conf.NodeSelector)

	if trainingCR.Spec.Resources.Requests.GPU == nil {
		tolerationConf := viper.GetStringMapString(train_conf.Toleration)
		if tolerationConf != nil {
			tolerations = append(tolerations, corev1.Toleration{
				Key:      tolerationConf[train_conf.TolerationKey],
				Operator: corev1.TolerationOperator(tolerationConf[train_conf.TolerationOperator]),
				Value:    tolerationConf[train_conf.TolerationValue],
				Effect:   corev1.TaintEffect(tolerationConf[train_conf.TolerationEffect]),
			})
		}
	}

	trainPod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      trainingCR.Name,
			Namespace: viper.GetString(train_conf.Namespace),
		},
		Spec: corev1.PodSpec{
			RestartPolicy:                 corev1.RestartPolicyNever,
			ServiceAccountName:            viper.GetString(train_conf.TrainingServiceAccount),
			TerminationGracePeriodSeconds: &terminationGracePeriodSeconds,
			NodeSelector:                  nodeSelector,
			Tolerations:                   tolerations,
			Volumes: []corev1.Volume{
				{
					Name: gitSecretVolumeName,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{
							SecretName:  legion.GenerateConnectionSecretName(trainingCR.Spec.VCSName),
							DefaultMode: &secretDefaultMode,
						},
					},
				},
				{
					Name: configVolume,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{
							SecretName:  trainingCR.Name,
							DefaultMode: &secretDefaultMode,
						},
					},
				},
				{
					Name: gitSSHVolumeName,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{
							SecretName:  legion.GenerateConnectionSecretName(trainingCR.Spec.VCSName),
							DefaultMode: &secretDefaultMode,
						},
					},
				},
			},
			Containers: []corev1.Container{
				{
					Name:  containerName,
					Image: viper.GetString(train_conf.ModelBuilderImage),
					Command: []string{
						TrainStartCommand,
					},
					Args: []string{
						"--mt-file", MtConfig, "--config", TrainConfigPath,
					},
					Resources: mtResources,
					VolumeMounts: []corev1.VolumeMount{
						{
							MountPath: gitSecretPath,
							Name:      gitSecretVolumeName,
						},
						{
							MountPath: configDir,
							Name:      configVolume,
						},
						{
							MountPath: gitSSHVolumePath,
							Name:      gitSSHVolumeName,
						},
					},
					SecurityContext: &corev1.SecurityContext{
						Privileged:               &trainingPrivileged,
						AllowPrivilegeEscalation: &trainingPrivileged,
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(trainingCR, trainPod, r.scheme); err != nil {
		return nil, err
	}

	if err := legion.StoreHash(trainPod); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return nil, err
	}

	found := &corev1.Pod{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: trainPod.Name, Namespace: viper.GetString(train_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s secret", trainPod.ObjectMeta.Name))
		return trainPod, r.Create(context.TODO(), trainPod)
	} else if err != nil {
		return nil, err
	}

	if err := r.Delete(context.TODO(), trainPod); err != nil {
		return nil, err
	}

	return trainPod, r.Create(context.TODO(), trainPod)
}

func (r *ReconcileModelTraining) reconcileConfig(trainingCR *legionv1alpha1.ModelTraining) error {
	vcs, err := r.getVcsConnection(trainingCR)
	if err != nil {
		return err
	}

	inputData, err := r.generateInputData(trainingCR)
	if err != nil {
		return err
	}

	outputConn, err := r.getOutputConnection()
	if err != nil {
		return err
	}

	ti, err := r.getToolchainIntegration(trainingCR)
	if err != nil {
		return err
	}

	k8sTraining := &training.K8sTrainer{
		VCS:        vcs,
		InputData:  inputData,
		OutputConn: outputConn,
		ModelTraining: &training.ModelTraining{
			ID:   trainingCR.Name,
			Spec: trainingCR.Spec,
		},
		ToolchainIntegration: ti,
	}

	k8sTrainingBytes, err := json.Marshal(k8sTraining)
	if err != nil {
		return err
	}

	conf := &BuilderConf{}
	conf.Builder.SSHKeyPath = path.Join("/home/root/.ssh/", trainer.GitSSHKeyFileName)

	trainerConfBytes, err := json.Marshal(conf)
	if err != nil {
		return err
	}

	k8sTrainingSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      trainingCR.Name,
			Namespace: viper.GetString(train_conf.Namespace),
		},
		Data: map[string][]byte{
			"mt.json":           k8sTrainingBytes,
			"trainer.conf.yaml": trainerConfBytes,
		},
	}

	if err := controllerutil.SetControllerReference(trainingCR, k8sTrainingSecret, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(k8sTrainingSecret); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.Secret{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: trainingCR.Name, Namespace: viper.GetString(train_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s secret", k8sTrainingSecret.ObjectMeta.Name))
		err = r.Create(context.TODO(), k8sTrainingSecret)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(k8sTrainingSecret, found) {
		log.Info(fmt.Sprintf(
			"Knative Configuration hashes don't equal. Update the %s training config",
			k8sTrainingSecret.Name,
		))

		found.Data = k8sTrainingSecret.Data

		log.Info(fmt.Sprintf("Updating %s training config", k8sTrainingSecret.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf(
			"training config hashes equal. Skip updating of the %s training config", k8sTrainingSecret.Name,
		))
	}

	return nil
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
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=packagingintegrations,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=packagingintegrations/status,verbs=get;update;patch
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

	if err := r.reconcileConfig(trainingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S secret state to cluster")

		return reconcile.Result{}, err
	}

	if trainPod, err := r.reconcilePod(trainingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S instances state to cluster")

		return reconcile.Result{}, err
	} else if err := r.syncCrdState(trainPod, trainingCR); err != nil {
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
