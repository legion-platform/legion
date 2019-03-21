/*

   Copyright 2019 EPAM Systems

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

*/

package modeltraining

import (
	"context"
	"fmt"

	legionv1alpha1 "github.com/legion-platform/legion/legion-operator/pkg/apis/legion/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
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

var log = logf.Log.WithName("controller")

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

// ReconcileModelTraining reconciles a ModelTraining object
type ReconcileModelTraining struct {
	client.Client
	scheme   *runtime.Scheme
	recorder record.EventRecorder
}

const (
	secretNameTemplate  = "%s-training-secret"
	podNameTemplate     = "%s-training-pod"
	gitSecretVolumeName = "git-secrets"
	gitSecretPath       = "/home/root/.ssh"
)

// FindVCSInstance finds relevant VCS instance for ModelTraining instance
func FindVCSInstance(r *ReconcileModelTraining, instance *legionv1alpha1.ModelTraining, vcsInstance *legionv1alpha1.VCSCredential) error {
	instanceLog := log.WithValues("mt-namespace", instance.Namespace, "mt-name", instance.Name)

	vcsInstanceName := types.NamespacedName{
		Name:      instance.Spec.VCSName,
		Namespace: instance.Namespace,
	}

	if err := r.Get(context.TODO(), vcsInstanceName, vcsInstance); err != nil {
		instanceLog.Error(err, "Cannot fetch VCS Credential with name", vcsInstanceName)
		r.recorder.Event(instance, "Warning", "CannotFetch",
			fmt.Sprintf("Cannot find VCS Credential %s. Updation ignored", vcsInstanceName))

		// Error reading the object - requeue the request.
		return err
	}

	return nil
}

// BuildK8SItems builds Pod and Secret for ModelTraining instance
func BuildK8SItems(r *ReconcileModelTraining, instance *legionv1alpha1.ModelTraining, pod *corev1.Pod, secret *corev1.Secret) error {
	instanceLog := log.WithValues("mt-namespace", instance.Namespace, "mt-name", instance.Name)

	vcsInstance := &legionv1alpha1.VCSCredential{}

	if err := FindVCSInstance(r, instance, vcsInstance); err != nil {
		return err
	}

	if vcsInstance.Spec.VCSCreds != "" {
		*secret = corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      fmt.Sprintf(secretNameTemplate, instance.Name),
				Namespace: instance.Namespace,
			},
			Data: map[string][]byte{
				"id_rsa": []byte(vcsInstance.Spec.VCSCreds),
			},
		}
	}

	*pod = corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf(podNameTemplate, instance.Name),
			Namespace: instance.Namespace,
		},
		Spec: corev1.PodSpec{
			Containers: []corev1.Container{
				{
					Name:  "training",
					Image: "nginx",
				},
			},
		},
	}

	// Add refs in pod to secret, link secret with CR
	if secret != nil {
		// Add volume
		pod.Spec.Volumes = append(pod.Spec.Volumes, corev1.Volume{
			Name: gitSecretVolumeName,
			VolumeSource: corev1.VolumeSource{
				Secret: &corev1.SecretVolumeSource{ //+safeToCommit
					SecretName: fmt.Sprintf(secretNameTemplate, instance.Name),
				},
			},
		})

		// Add volume mount
		pod.Spec.Containers[0].VolumeMounts = append(pod.Spec.Containers[0].VolumeMounts, corev1.VolumeMount{
			Name:      gitSecretVolumeName,
			ReadOnly:  true,
			MountPath: gitSecretPath,
		})

		if err := controllerutil.SetControllerReference(instance, secret, r.scheme); err != nil {
			instanceLog.Error(err, "Cannot attach owner info to Secret")
			return err
		}
	}

	if err := controllerutil.SetControllerReference(instance, pod, r.scheme); err != nil {
		log.Error(err, "Cannot attach owner info to Pod")
		return err
	}

	return nil
}

// SyncronizeK8SInstances updates K8S instances to match desired state
func SyncronizeK8SInstances(r *ReconcileModelTraining, instance *legionv1alpha1.ModelTraining, pod *corev1.Pod, secret *corev1.Secret) (bool, error) {
	instanceLog := log.WithValues("mt-namespace", instance.Namespace, "mt-name", instance.Name)

	anyInstanceCreated := false
	foundSecret := corev1.Secret{}
	foundPod := corev1.Pod{}

	// Create secret or fail (if it is not created yet)
	if secret != nil {
		secretNamespacedName := types.NamespacedName{Name: secret.Name, Namespace: secret.Namespace}
		if err := r.Get(context.TODO(), secretNamespacedName, &foundSecret); err != nil && errors.IsNotFound(err) {
			// If can not find Secret
			instanceLog.Info("Creating SVC secret", "name", secretNamespacedName)
			err = r.Create(context.TODO(), secret)
			if err != nil {
				// If cannot create secret
				instanceLog.Error(err, "Cannot create Secret")
				r.recorder.Event(instance, "Warning", "CannotSpawn",
					fmt.Sprintf("Cannot create Secret %s. Failed", secretNamespacedName))
				return anyInstanceCreated, err
			}

			instanceLog.Info("Secret created")
			r.recorder.Event(instance, "Normal", "Spawning",
				fmt.Sprintf("Creating Secret %s", secretNamespacedName))
			*secret = foundSecret
			anyInstanceCreated = true

		} else if err != nil {
			instanceLog.Error(err, "Cannot fetch secrets")
			return anyInstanceCreated, err
		}
	}

	podNamespacedName := types.NamespacedName{Name: pod.Name, Namespace: pod.Namespace}
	// Create pod & return or fail (if it is not created yet)
	if err := r.Get(context.TODO(), podNamespacedName, &foundPod); err != nil && errors.IsNotFound(err) {
		// If can not find Pod
		instanceLog.Info("Creating pod", podNamespacedName)

		err = r.Create(context.TODO(), pod)
		if err != nil {
			// If error during Pod creation
			instanceLog.Error(err, "Cannot create Pod")
			r.recorder.Event(instance, "Warning", "CannotSpawn",
				fmt.Sprintf("Cannot create Pod %s. Failed", podNamespacedName))
			return anyInstanceCreated, err
		}

		// If no errors during Pod creation
		instanceLog.Info("Created Pod")
		r.recorder.Event(instance, "Normal", "Spawning",
			fmt.Sprintf("Creating Pod %s", podNamespacedName))
		anyInstanceCreated = true
		*pod = foundPod
	} else if err != nil {
		// If cannot gather Pod information
		instanceLog.Error(err, "Cannot fetch actual pods")
		return anyInstanceCreated, err
	}

	return anyInstanceCreated, nil
}

// SyncronizeK8SState syncronize state of ModelTraining instance based on child instances
func SyncronizeK8SState(r *ReconcileModelTraining, instance *legionv1alpha1.ModelTraining, pod *corev1.Pod, secret *corev1.Secret) error {
	instanceLog := log.WithValues("mt-namespace", instance.Namespace, "mt-name", instance.Name)

	switch pod.Status.Phase {
	case corev1.PodPending:
		instance.Status.TrainingState = legionv1alpha1.ModelTrainingScheduling
	case corev1.PodRunning:
		instance.Status.TrainingState = legionv1alpha1.ModelTrainingRunning
	case corev1.PodSucceeded:
		instance.Status.TrainingState = legionv1alpha1.ModelTrainingSucceeded
	case corev1.PodFailed:
		instance.Status.TrainingState = legionv1alpha1.ModelTrainingFailed
	case corev1.PodUnknown:
		instance.Status.TrainingState = legionv1alpha1.ModelTrainingUnknown
	}

	if err := r.Update(context.TODO(), instance); err != nil {
		instanceLog.Error(err, "Cannot update status of CR instance")
		return err
	}

	return nil
}

// Reconcile reads that state of the cluster for a ModelTraining object and makes changes based on the state read
// and what is in the ModelTraining.Spec
// +kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=pods/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeltrainings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=vcscredentials,verbs=get;list
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelTraining) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	instanceLog := log.WithValues("mt-namespace", request.Namespace, "mt-name", request.Name)

	// Fetch the ModelTraining instance
	instance := &legionv1alpha1.ModelTraining{}

	if err := r.Get(context.TODO(), request.NamespacedName, instance); err != nil {
		if errors.IsNotFound(err) {
			instanceLog.Error(err, "Cannot find CR instance for event")
			// Object not found, return.  Created objects are automatically garbage collected.
			// For additional cleanup logic use finalizers.
			return reconcile.Result{}, nil
		}
		instanceLog.Error(err, "Cannot fetch CR status")
		return reconcile.Result{}, err
	}

	// Define secret if it is not null
	var (
		pod    = &corev1.Pod{}
		secret = &corev1.Secret{}
	)

	if err := BuildK8SItems(r, instance, pod, secret); err != nil {
		instanceLog.Error(err, "Cannot build appropriate pod/secret state for model training instance")

		r.recorder.Event(instance, "Warning", "CannotProcess",
			"Cannot build appropriate pod/secret state. Updation ignored")

		return reconcile.Result{}, err
	}

	// Creation phase
	if created, err := SyncronizeK8SInstances(r, instance, pod, secret); err != nil {
		instanceLog.Error(err, "Can not syncronize desired K8S instances state to cluster")
		if created {
			instanceLog.Error(err, "Looks like some (but not all) resources have been created")
		}
		return reconcile.Result{}, err
	} else if created {
		instanceLog.Info("All resources has been created")
		return reconcile.Result{}, nil
	}

	// OK - instances syncronized. Now we can check & update statuses

	if err := SyncronizeK8SState(r, instance, pod, secret); err != nil {
		instanceLog.Error(err, "Can't syncronize K8S state")
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
