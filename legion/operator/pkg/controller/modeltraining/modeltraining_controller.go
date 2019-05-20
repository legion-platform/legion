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
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
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

var log = logf.Log.WithName("modeltraining_controller")

/**
* USER ACTION REQUIRED: This is a scaffold file intended for the user to modify with their own Controller
* business logic.  Delete these comments after modifying this file.*
 */

// Add creates a new ModelTraining Controller and adds it to the Manager with default RBAC. The Manager will set fields on the Controller
// and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return &ReconcileModelTraining{
		Client:   mgr.GetClient(),
		config:   mgr.GetConfig(),
		scheme:   mgr.GetScheme(),
		recorder: mgr.GetRecorder("legion-operator"),
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
	if err := c.Watch(&source.Kind{Type: &legionv1alpha1.ModelTraining{}}, &handler.EnqueueRequestForObject{}); err != nil {
		log.Error(err, "Cannot create watch for ModelTraining CR instances")
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Pod{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelTraining{},
	})
	if err != nil {
		log.Error(err, "Cannot create watch for ModelTraining CR children Pod instances")
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelTraining{}

var (
	builderResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	secretDefaultMode             = int32(420)
	terminationGracePeriodSeconds = int64(0)
)

// ReconcileModelTraining reconciles a ModelTraining object
type ReconcileModelTraining struct {
	client.Client
	scheme   *runtime.Scheme
	recorder record.EventRecorder
	config   *rest.Config
}

const (
	gitSecretVolumeName    = "git-secrets"
	gitSecretPath          = "/home/root/.ssh"
	sharedDirPath          = "/var/legion"
	sharedDirName          = "shared-dir"
	modelContainerName     = "model"
	dockerSocketVolumeName = "docker-socket"
	dockerSocketVolumePath = "/var/run/docker.sock"
	gitSshVolumeName       = "git-ssh"
	gitSshVolumePath       = "/etc/ssh"
	builderContainerName   = "builder"
)

// FindVCSInstance finds relevant VCS instance for ModelTraining instance
func (r *ReconcileModelTraining) findVCSInstance(vcsName string, namespace string) (vcsCR *legionv1alpha1.VCSCredential, err error) {
	vcsInstanceName := types.NamespacedName{
		Name:      vcsName,
		Namespace: namespace,
	}
	vcsCR = &legionv1alpha1.VCSCredential{}

	if err = r.Get(context.TODO(), vcsInstanceName, vcsCR); err != nil {
		log.Error(err, "Cannot fetch VCS Credential with name")

		return
	}

	return
}

func (r *ReconcileModelTraining) createModelBuildPod(modelBuilderCR *legionv1alpha1.ModelTraining) (pod *corev1.Pod, err error) {
	vcsInstance, err := r.findVCSInstance(modelBuilderCR.Spec.VCSName, modelBuilderCR.Namespace)
	if err != nil {
		log.Error(err, fmt.Sprintf("Finding vcs %s instanse", modelBuilderCR.Spec.VCSName))
		return nil, err
	}

	vcsSecretName := legion.GenerateVcsSecretName(vcsInstance.Name)

	modelCommand, err := legion.GenerateModelCommand(
		modelBuilderCR.Spec.WorkDir,
		modelBuilderCR.Spec.ToolchainType,
		modelBuilderCR.Spec.Entrypoint,
		modelBuilderCR.Spec.EntrypointArguments,
	)
	if err != nil {
		return nil, err
	}

	pod = &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      legion.GenerateBuildModelName(modelBuilderCR.Name),
			Namespace: modelBuilderCR.Namespace,
		},
		Spec: corev1.PodSpec{
			RestartPolicy:                 corev1.RestartPolicyNever,
			ServiceAccountName:            viper.GetString(legion.BuilderServiceAccount),
			TerminationGracePeriodSeconds: &terminationGracePeriodSeconds,
			Volumes: []corev1.Volume{
				{
					Name: gitSecretVolumeName,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{ //+safeToCommit
							SecretName:  vcsSecretName,
							DefaultMode: &secretDefaultMode,
						},
					},
				},
				{
					Name: sharedDirName,
					VolumeSource: corev1.VolumeSource{
						EmptyDir: &corev1.EmptyDirVolumeSource{},
					},
				},
				{
					Name: dockerSocketVolumeName,
					VolumeSource: corev1.VolumeSource{
						HostPath: &corev1.HostPathVolumeSource{
							Path: dockerSocketVolumePath,
						},
					},
				},
				{
					Name: gitSshVolumeName,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{ //+safeToCommit
							SecretName:  vcsSecretName,
							DefaultMode: &secretDefaultMode,
						},
					},
				},
			},
			Containers: []corev1.Container{
				{
					Name:    modelContainerName,
					Image:   modelBuilderCR.Spec.Image,
					Command: []string{"/bin/tiny"},
					Args:    []string{"--", "cat"},
					Stdin:   true,
					Env: []corev1.EnvVar{
						{
							Name: legion.Namespace,
							ValueFrom: &corev1.EnvVarSource{
								FieldRef: &corev1.ObjectFieldSelector{
									FieldPath: "metadata.namespace",
								},
							},
						},
						{
							Name:  legion.MetricHost,
							Value: viper.GetString(legion.MetricHost),
						},
						{
							Name:  legion.MetricPort,
							Value: viper.GetString(legion.MetricPort),
						},
						{
							Name:  legion.MetricEnabled,
							Value: viper.GetString(legion.MetricEnabled),
						},
						{
							Name:  legion.ModelFile,
							Value: modelBuilderCR.Spec.ModelFile,
						},
						{
							Name:  legion.DockerRegistry,
							Value: viper.GetString(legion.DockerRegistry),
						},
						{
							Name:  legion.DockerRegistryUser,
							Value: viper.GetString(legion.DockerRegistryUser),
						},
						{
							Name:  legion.DockerRegistryPassword,
							Value: viper.GetString(legion.DockerRegistryPassword),
						},
					},
					Resources: *modelBuilderCR.Spec.Resources,
					VolumeMounts: []corev1.VolumeMount{
						{
							MountPath: sharedDirPath,
							Name:      sharedDirName,
						},
						{
							MountPath: dockerSocketVolumePath,
							Name:      dockerSocketVolumeName,
						},
					},
				},
				{
					Name:  builderContainerName,
					Image: viper.GetString(legion.BuilderImage),
					Env: []corev1.EnvVar{
						{
							Name: legion.PodName,
							ValueFrom: &corev1.EnvVarSource{
								FieldRef: &corev1.ObjectFieldSelector{
									FieldPath: "metadata.name",
								},
							},
						},
						{
							Name: legion.Namespace,
							ValueFrom: &corev1.EnvVarSource{
								FieldRef: &corev1.ObjectFieldSelector{
									FieldPath: "metadata.namespace",
								},
							},
						},
						{
							Name:  legion.RepositoryURL,
							Value: vcsInstance.Spec.Uri,
						},
						{
							Name:  legion.ImagePrefix,
							Value: viper.GetString(legion.ImagePrefix),
						},
						{
							Name:  legion.SharedDirPath,
							Value: sharedDirPath,
						},
						{
							Name:  legion.Reference,
							Value: modelBuilderCR.Spec.Reference,
						},
						{
							Name:  legion.ModelFile,
							Value: modelBuilderCR.Spec.ModelFile,
						},
						{
							Name:  legion.ModelCommand,
							Value: modelCommand,
						},
						{
							Name:  legion.DockerRegistry,
							Value: viper.GetString(legion.DockerRegistry),
						},
						{
							Name:  legion.DockerRegistryUser,
							Value: viper.GetString(legion.DockerRegistryUser),
						},
						{
							Name:  legion.DockerRegistryPassword,
							Value: viper.GetString(legion.DockerRegistryPassword),
						},
						{
							Name:  legion.GitSSHKeyPath,
							Value: fmt.Sprintf("%s/%s", gitSecretPath, utils.GitSSHKeyFileName),
						},
					},
					Resources: builderResources,
					VolumeMounts: []corev1.VolumeMount{
						{
							MountPath: sharedDirPath,
							Name:      sharedDirName,
						},
						{
							MountPath: gitSecretPath,
							Name:      gitSecretVolumeName,
						},
						{
							MountPath: dockerSocketVolumePath,
							Name:      dockerSocketVolumeName,
						},
						{
							MountPath: gitSshVolumePath,
							Name:      gitSshVolumeName,
						},
					},
				},
			},
		},
	}

	if err = controllerutil.SetControllerReference(modelBuilderCR, pod, r.scheme); err != nil {
		log.Error(err, "Cannot attach owner info to Secret")
		return
	}

	return pod, nil
}

func (r *ReconcileModelTraining) syncK8SInstances(modelBuilderCR *legionv1alpha1.ModelTraining) (err error) {
	log.Info(fmt.Sprintf("%+v", modelBuilderCR.Status))

	if isModelBuildCompleted(modelBuilderCR) {
		return nil
	}

	modelBuilderPod, err := r.createModelBuildPod(modelBuilderCR)
	if err != nil {
		log.Error(err, "Create model builder pod")

		return err
	}

	podNamespacedName := types.NamespacedName{Name: modelBuilderPod.Name, Namespace: modelBuilderCR.Namespace}

	if err = r.Get(context.TODO(), podNamespacedName, modelBuilderPod); err != nil && errors.IsNotFound(err) {
		log.Info("Creating pod")

		err = r.Create(context.TODO(), modelBuilderPod)
		if err != nil {
			log.Error(err, "Cannot create Pod")

			r.recorder.Event(modelBuilderCR, "Warning", "CannotSpawn",
				fmt.Sprintf("Cannot create Pod %s. Failed", podNamespacedName))

			return
		}

		log.Info("Created Pod")
	} else if err != nil {
		log.Error(err, "Cannot fetch actual pods")
		return
	}

	err = r.syncCrdState(modelBuilderPod, modelBuilderCR)
	if err != nil {
		log.Error(err, "Sync ModelBuilder crd state")
		return
	} else {
		modelBuilderCR.Status.PodName = modelBuilderCR.Name
	}

	if modelBuilderCR.Status.TrainingState == legionv1alpha1.ModelTrainingSucceeded {
		err = r.Delete(context.TODO(), modelBuilderPod)

		if err != nil && !errors.IsNotFound(err) {
			log.Error(err, fmt.Sprintf("Delete %s model builder pod", modelBuilderPod.Name))
			return err
		}

		log.Info(fmt.Sprintf("%s model builder pod was deleted", modelBuilderPod.Name))
	}

	if modelBuilderCR.Status.TrainingState == legionv1alpha1.ModelTrainingFailed {
		err := utils.ExecToPodThroughAPI(
			[]string{"/bin/kill", "1"},
			modelContainerName,
			modelBuilderPod.Name,
			modelBuilderCR.Namespace,
			r.config,
		)

		if err != nil {
			log.Error(err, "Cannot kill the model container")
			return err
		}
	}

	log.Info(fmt.Sprintf("Update crd: %+v", modelBuilderCR))

	if err := r.Update(context.TODO(), modelBuilderCR); err != nil {
		log.Error(err, "Cannot update status of CR modelBuilderCr")
		return err
	}

	return
}

// Determine crd state by child pod.
// If pod has RUNNING state then we determine crd state by state of builder container in the pod
func (r *ReconcileModelTraining) syncCrdState(pod *corev1.Pod, modelCrd *legionv1alpha1.ModelTraining) error {
	switch pod.Status.Phase {
	case corev1.PodPending:
		modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingScheduling
	case corev1.PodRunning:
		for _, container := range pod.Status.ContainerStatuses {
			if container.Name == "builder" {
				if container.State.Running != nil {
					modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingRunning
				} else if container.State.Terminated != nil {
					if container.State.Terminated.ExitCode == 0 {
						modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingSucceeded
						modelCrd.Status.ModelImage = pod.Annotations[legion.ModelImageKey]

						modelId := pod.Annotations[legion.ModelIDKey]
						modelVersion := pod.Annotations[legion.ModelVersionKey]

						if modelCrd.ObjectMeta.Labels == nil {
							modelCrd.ObjectMeta.Labels = map[string]string{}
						}

						modelCrd.ObjectMeta.Labels[legion.DomainModelId] = modelId
						modelCrd.ObjectMeta.Labels[legion.DomainModelVersion] = modelVersion

						modelCrd.Status.ModelID = modelId
						modelCrd.Status.ModelVersion = modelVersion
					} else {
						modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingFailed
					}

					modelCrd.Status.Message = container.State.Terminated.Message
					modelCrd.Status.ExitCode = container.State.Terminated.ExitCode
					modelCrd.Status.Reason = container.State.Terminated.Reason
				} else {
					modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingScheduling
				}
			} else {
				log.Info(fmt.Sprintf("Skip processing of %s container with %+v state",
					container.Name, container.State))
			}
		}
	case corev1.PodSucceeded:
		modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingSucceeded
	case corev1.PodFailed:
		modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingFailed
	case corev1.PodUnknown:
		modelCrd.Status.TrainingState = legionv1alpha1.ModelTrainingUnknown
	}

	return nil
}

// Reconcile reads that state of the cluster for a ModelTraining object and makes changes based on the state read
// and what is in the ModelTraining.Spec
// +kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=pods/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=pods/exec,verbs=create
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=vcscredentials,verbs=get;list
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelTraining) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ModelTraining modelBuilderCrd
	modelBuilderCrd := &legionv1alpha1.ModelTraining{}

	if err := r.Get(context.TODO(), request.NamespacedName, modelBuilderCrd); err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}
		log.Error(err, "Cannot fetch CR status")
		return reconcile.Result{}, err
	}

	if err := r.syncK8SInstances(modelBuilderCrd); err != nil {
		log.Error(err, "Can not synchronize desired K8S instances state to cluster")

		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}

func isModelBuildCompleted(crd *legionv1alpha1.ModelTraining) bool {
	return crd.Status.TrainingState == legionv1alpha1.ModelTrainingSucceeded ||
		crd.Status.TrainingState == legionv1alpha1.ModelTrainingFailed
}
