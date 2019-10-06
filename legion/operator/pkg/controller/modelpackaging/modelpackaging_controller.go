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
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	conn_conf "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	packaging_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/rest"
	"path"
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
	return &ReconcileModelPackaging{Client: mgr.GetClient(), scheme: mgr.GetScheme(), config: mgr.GetConfig()}
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

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelPackaging{}

// ReconcileModelPackaging reconciles a ModelPackaging object
type ReconcileModelPackaging struct {
	client.Client
	scheme *runtime.Scheme
	config *rest.Config
}

const (
	sharedDir             = "/opt/legion/target"
	packagerContainerName = "packager"
	modelContainerName    = "model"
	sharedVolumeName      = "shared"
	configVolumeName      = "config"
	packagerCommand       = "/opt/legion/packager"
	configVolumePath      = "/etc/legion"
	mpContentFile         = "mp.json"
	packagerConfig        = "packager.conf.yaml"
	evictedPodReason      = "Evicted"
)

var (
	packagerResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
	}
	tinyCommand                   = []string{"/bin/tiny"}
	tinyArgs                      = []string{"--", "cat"}
	secretDefaultMode             = int32(420)
	terminationGracePeriodSeconds = int64(0)
	packagingPrivileged           = true
)

// FindVCSInstance finds relevant VCS instance for ModelPackaging instance
func (r *ReconcileModelPackaging) findConnection(connName string) (vcsCR *legionv1alpha1.Connection, err error) {
	vcsInstanceName := types.NamespacedName{
		Name:      connName,
		Namespace: viper.GetString(conn_conf.Namespace),
	}
	vcsCR = &legionv1alpha1.Connection{}

	if err = r.Get(context.TODO(), vcsInstanceName, vcsCR); err != nil {
		log.Error(err, "Cannot fetch VCS Credential with name")

		return
	}

	return
}

// Determine crd state by child pod.
// If pod has RUNNING state then we determine crd state by state of packager container in the pod
func (r *ReconcileModelPackaging) syncCrdState(pod *corev1.Pod, packagingCR *legionv1alpha1.ModelPackaging) error {
	switch pod.Status.Phase {
	case corev1.PodPending:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
	case corev1.PodRunning:
		fallthrough
	case corev1.PodSucceeded:
		fallthrough
	case corev1.PodFailed:
		calculateResult(pod, packagingCR)
	case corev1.PodUnknown:
		packagingCR.Status.State = legionv1alpha1.ModelPackagingUnknown
	}

	if packagingCR.Status.State == legionv1alpha1.ModelPackagingFailed ||
		packagingCR.Status.State == legionv1alpha1.ModelPackagingSucceeded {
		for _, container := range pod.Status.ContainerStatuses {
			if container.Name == "model" {
				if container.State.Running != nil {
					if err := r.killModelContainer(packagingCR); err != nil {
						return err
					}
				}
			} else {
				log.Info(fmt.Sprintf("Skip processing of %s container with %+v state",
					container.Name, container.State))
			}
		}
	}

	if err := r.Update(context.TODO(), packagingCR); err != nil {
		return err
	}

	return nil
}

func calculateResult(pod *corev1.Pod, packagingCR *legionv1alpha1.ModelPackaging) {
	if pod.Status.Reason == evictedPodReason {
		packagingCR.Status.State = legionv1alpha1.ModelPackagingFailed
		packagingCR.Status.Message = &pod.Status.Message

		return
	}

	for _, container := range pod.Status.ContainerStatuses {
		if container.Name == "packager" {
			switch {
			case container.State.Running != nil:
				packagingCR.Status.State = legionv1alpha1.ModelPackagingRunning
			case container.State.Terminated != nil:
				if container.State.Terminated.ExitCode == 0 {
					packagingCR.Status.State = legionv1alpha1.ModelPackagingSucceeded
				} else {
					packagingCR.Status.State = legionv1alpha1.ModelPackagingFailed
				}

				if packagingCR.Status.Results == nil {
					packagingCR.Status.Results = []legionv1alpha1.ModelPackagingResult{}
				}

				for key, value := range pod.Annotations {
					if key != legion.LastAppliedHashAnnotation {
						packagingCR.Status.Results = append(packagingCR.Status.Results,
							legionv1alpha1.ModelPackagingResult{
								Name:  key,
								Value: value,
							})
					}
				}

				packagingCR.Status.Message = &container.State.Terminated.Message
				packagingCR.Status.ExitCode = &container.State.Terminated.ExitCode
				packagingCR.Status.Reason = &container.State.Terminated.Reason
			default:
				packagingCR.Status.State = legionv1alpha1.ModelPackagingScheduling
			}
		} else {
			log.Info(fmt.Sprintf("Skip processing of %s container with %+v state",
				container.Name, container.State))
		}
	}
}

func (r *ReconcileModelPackaging) getOutputConnection() (*connection.Connection, error) {
	vcs := &legionv1alpha1.Connection{}
	if err := r.Get(context.TODO(), types.NamespacedName{
		Namespace: viper.GetString(conn_conf.Namespace),
		Name:      viper.GetString(packaging_conf.OutputConnectionName),
	}, vcs); err != nil {
		log.Error(err, "Get output connection", "vcs name", vcs)
		return nil, err
	}
	return &connection.Connection{
		ID:   viper.GetString(packaging_conf.OutputConnectionName),
		Spec: vcs.Spec,
	}, nil
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

func (r *ReconcileModelPackaging) reconcilePod(packagingCR *legionv1alpha1.ModelPackaging) (*corev1.Pod, error) {
	if packagingCR.Status.State != "" && packagingCR.Status.State != legionv1alpha1.ModelPackagingUnknown {
		pod := &corev1.Pod{}
		err := r.Get(context.TODO(), types.NamespacedName{
			Name: packagingCR.Name, Namespace: viper.GetString(packaging_conf.Namespace),
		}, pod)
		if err != nil {
			return nil, err
		}

		log.Info("Packaging has no unknown state. Skip the pod reconcile",
			"mt id", packagingCR.Name, "state", packagingCR.Status.State)
		return pod, nil
	}

	tolerations := []corev1.Toleration{}
	tolerationConf := viper.GetStringMapString(packaging_conf.Toleration)
	if tolerationConf != nil {
		tolerations = append(tolerations, corev1.Toleration{
			Key:      tolerationConf[packaging_conf.TolerationKey],
			Operator: corev1.TolerationOperator(tolerationConf[packaging_conf.TolerationOperator]),
			Value:    tolerationConf[packaging_conf.TolerationValue],
			Effect:   corev1.TaintEffect(tolerationConf[packaging_conf.TolerationEffect]),
		})
	}

	packResources, err := kubernetes.ConvertLegionResourcesToK8s(packagingCR.Spec.Resources)
	if err != nil {
		log.Error(err, "The packaging resources is not valid",
			"mp id", packagingCR.Name, "resources", packagingCR.Namespace)

		return nil, err
	}

	packagerPod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      packagingCR.Name,
			Namespace: viper.GetString(packaging_conf.Namespace),
		},
		Spec: corev1.PodSpec{
			RestartPolicy:                 corev1.RestartPolicyNever,
			ServiceAccountName:            viper.GetString(packaging_conf.ServiceAccount),
			TerminationGracePeriodSeconds: &terminationGracePeriodSeconds,
			NodeSelector:                  viper.GetStringMapString(packaging_conf.NodeSelector),
			Tolerations:                   tolerations,
			Volumes: []corev1.Volume{
				{
					Name: sharedVolumeName,
					VolumeSource: corev1.VolumeSource{
						EmptyDir: &corev1.EmptyDirVolumeSource{},
					},
				},
				{
					Name: configVolumeName,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{
							SecretName:  packagingCR.Name,
							DefaultMode: &secretDefaultMode,
						},
					},
				},
			},
			Containers: []corev1.Container{
				{
					Name:      modelContainerName,
					Resources: packResources,
					Image:     packagingCR.Spec.Image,
					Command:   tinyCommand,
					Args:      tinyArgs,
					Stdin:     true,
					VolumeMounts: []corev1.VolumeMount{
						{
							MountPath: sharedDir,
							Name:      sharedVolumeName,
						},
					},
					Env: []corev1.EnvVar{},
					SecurityContext: &corev1.SecurityContext{
						Privileged:               &packagingPrivileged,
						AllowPrivilegeEscalation: &packagingPrivileged,
					},
				},
				{
					Name:  packagerContainerName,
					Image: viper.GetString(packaging_conf.ModelPackagerImage),
					Command: []string{
						packagerCommand,
					},
					Args: []string{
						"--mt-file", path.Join(configVolumePath, mpContentFile),
						"--config", path.Join(configVolumePath, packagerConfig),
					},
					Resources: packagerResources,
					VolumeMounts: []corev1.VolumeMount{
						{
							MountPath: sharedDir,
							Name:      sharedVolumeName,
						},
						{
							MountPath: configVolumePath,
							Name:      configVolumeName,
						},
					},
					SecurityContext: &corev1.SecurityContext{
						Privileged:               &packagingPrivileged,
						AllowPrivilegeEscalation: &packagingPrivileged,
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(packagingCR, packagerPod, r.scheme); err != nil {
		return nil, err
	}

	if err := legion.StoreHash(packagerPod); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return nil, err
	}

	found := &corev1.Pod{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: packagerPod.Name, Namespace: viper.GetString(packaging_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s secret", packagerPod.ObjectMeta.Name))
		return packagerPod, r.Create(context.TODO(), packagerPod)
	} else if err != nil {
		return nil, err
	}

	if err := r.Delete(context.TODO(), found); err != nil {
		return nil, err
	}

	return packagerPod, r.Create(context.TODO(), packagerPod)
}

type PackagerConf struct {
	Packager struct {
		PodName    string `json:"pod_name"`
		TargetPath string `json:"target_path"`
		OutputDir  string `json:"output_dir"`
	} `json:"packager"`
}

func (r *ReconcileModelPackaging) reconcileConfig(packagingCR *legionv1alpha1.ModelPackaging) error {
	outputConn, err := r.getOutputConnection()
	if err != nil {
		return err
	}

	pi, err := r.getPackagingIntegration(packagingCR)
	if err != nil {
		return err
	}

	mp, err := mp_k8s_repository.TransformMpFromK8s(packagingCR)
	if err != nil {
		return err
	}

	targets := make([]packaging.PackagerTarget, len(mp.Spec.Targets))
	for i, target := range mp.Spec.Targets {
		conn, err := r.findConnection(target.ConnectionName)
		if err != nil {
			return err
		}

		targets[i] = packaging.PackagerTarget{
			Name: target.Name,
			Connection: connection.Connection{
				ID:   conn.Name,
				Spec: conn.Spec,
			},
		}
	}

	k8sPackaging := &packaging.K8sPackager{
		ModelHolder:          outputConn,
		ModelPackaging:       mp,
		PackagingIntegration: pi,
		TrainingZipName:      *packagingCR.Spec.ArtifactName,
		Targets:              targets,
	}

	k8sPackagingBytes, err := json.Marshal(k8sPackaging)
	if err != nil {
		return err
	}

	conf := &PackagerConf{}
	conf.Packager.PodName = packagingCR.Name
	conf.Packager.TargetPath = path.Join(sharedDir, "shared")
	conf.Packager.OutputDir = path.Join(conf.Packager.TargetPath, "output")

	packagerConfBytes, err := json.Marshal(conf)
	if err != nil {
		return err
	}

	k8sPackagingSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      packagingCR.Name,
			Namespace: viper.GetString(packaging_conf.Namespace),
		},
		Data: map[string][]byte{
			mpContentFile:  k8sPackagingBytes,
			packagerConfig: packagerConfBytes,
		},
	}

	if err := controllerutil.SetControllerReference(packagingCR, k8sPackagingSecret, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(k8sPackagingSecret); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.Secret{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: packagingCR.Name, Namespace: viper.GetString(packaging_conf.Namespace),
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s secret", k8sPackagingSecret.ObjectMeta.Name))
		err = r.Create(context.TODO(), k8sPackagingSecret)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(k8sPackagingSecret, found) {
		log.Info(fmt.Sprintf(
			"Model packaging config hashes don't equal. Update the %s packaging config",
			k8sPackagingSecret.Name,
		))

		found.Data = k8sPackagingSecret.Data

		log.Info(fmt.Sprintf("Updating %s packaging config", k8sPackagingSecret.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf(
			"Model packaging config hashes equal. Skip updating of the %s packaging config",
			k8sPackagingSecret.Name,
		))
	}

	return nil
}

func isPackagingFinished(mp *legionv1alpha1.ModelPackaging) bool {
	state := mp.Status.State

	return state == legionv1alpha1.ModelPackagingSucceeded || state == legionv1alpha1.ModelPackagingFailed
}

func (r *ReconcileModelPackaging) killModelContainer(packagingCR *legionv1alpha1.ModelPackaging) error {
	err := utils.ExecToPodThroughAPI(
		[]string{"/bin/kill", "1"},
		"model",
		packagingCR.Name,
		packagingCR.Namespace,
		r.config,
	)

	if err != nil {
		log.Error(err, "Cannot kill the model container")
	}

	return err
}

// Reconcile reads that state of the cluster for a ModelPackaging object and makes changes based on the state read
// and what is in the ModelPackaging.Spec
// +kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=pods/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=pods/exec,verbs=create
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelpackagings/status,verbs=get;update;patch
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

	if err := r.reconcileConfig(packagingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S secret state to cluster")

		return reconcile.Result{}, err
	}

	if pod, err := r.reconcilePod(packagingCR); err != nil {
		log.Error(err, "Can not synchronize desired K8S instances state to cluster")

		return reconcile.Result{}, err
	} else if err := r.syncCrdState(pod, packagingCR); err != nil {
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
