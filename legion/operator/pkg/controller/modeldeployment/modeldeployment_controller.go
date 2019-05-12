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

package modeldeployment

import (
	"context"
	"fmt"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/record"
	"reflect"
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
	labelSelectorKey                 = "deployment"
	controllerName                   = "modeldeployemnt-controller"
	defaultModelPort                 = 5000
	defaultLivenessFailureThreshold  = 10
	defaultLivenessPeriod            = 10
	defaultLivenessTimeout           = 2
	defaultReadinessFailureThreshold = 5
	defaultReadinessPeriod           = 10
	defaultReadinessTimeout          = 2
	defaultModelPortName             = "api"
	modelContainerName               = "model"
)

var (
	log = logf.Log.WithName(controllerName)
)

func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return newConfigurableReconciler(mgr, utils.ExtractDockerLabels)
}

func newConfigurableReconciler(mgr manager.Manager, labelExtractor utils.LabelExtractor) reconcile.Reconciler {
	return &ReconcileModelDeployment{
		Client:         mgr.GetClient(),
		scheme:         mgr.GetScheme(),
		labelExtractor: labelExtractor,
		recorder:       mgr.GetRecorder(controllerName),
	}
}

func add(mgr manager.Manager, r reconcile.Reconciler) error {
	// Create a new controller
	c, err := controller.New(controllerName, mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	// Watch for changes to ModelDeployment
	err = c.Watch(&source.Kind{Type: &legionv1alpha1.ModelDeployment{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &appsv1.Deployment{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelDeployment{},
	})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Service{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelDeployment{},
	})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelDeployment{}

// ReconcileModelDeployment reconciles a ModelDeployment object
type ReconcileModelDeployment struct {
	client.Client
	scheme         *runtime.Scheme
	labelExtractor utils.LabelExtractor
	recorder       record.EventRecorder
}

type modelContainerMetaInformation struct {
	k8sName        string
	modelId        string
	modelVersion   string
	k8sLabels      map[string]string
	k8sAnnotations map[string]string
}

func (r *ReconcileModelDeployment) reconcileService(modelContainerMeta *modelContainerMetaInformation,
	modelDeploymentCR *legionv1alpha1.ModelDeployment) error {

	modelService := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:        modelContainerMeta.k8sName,
			Namespace:   modelDeploymentCR.Namespace,
			Labels:      modelContainerMeta.k8sLabels,
			Annotations: modelContainerMeta.k8sAnnotations,
		},
		Spec: corev1.ServiceSpec{
			Selector: modelContainerMeta.k8sLabels,
			Ports: []corev1.ServicePort{
				{
					Name:       defaultModelPortName,
					Protocol:   corev1.ProtocolTCP,
					TargetPort: intstr.FromString(defaultModelPortName),
					Port:       int32(defaultModelPort),
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, modelService, r.scheme); err != nil {
		return err
	}

	found := &corev1.Service{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: modelService.Name, Namespace: modelService.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s service", modelService.ObjectMeta.Name))
		err = r.Create(context.TODO(), modelService)
		return err
	} else if err != nil {
		return err
	}

	if !reflect.DeepEqual(modelService.Spec, found.Spec) {
		modelService.Spec.ClusterIP = found.Spec.ClusterIP
		found.Spec = modelService.Spec
		log.Info(fmt.Sprintf("Updating %s k8s service", modelService.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	}

	return nil
}

func (r *ReconcileModelDeployment) reconcileDeployment(modelContainerMeta *modelContainerMetaInformation,
	modelDeploymentCR *legionv1alpha1.ModelDeployment) error {

	httpGetAction := &corev1.HTTPGetAction{
		Path: "/healthcheck",
		Port: intstr.FromInt(defaultModelPort),
	}

	modelContainerMeta.k8sAnnotations[labelSelectorKey] = modelContainerMeta.k8sName

	modelDeployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:        modelContainerMeta.k8sName,
			Namespace:   modelDeploymentCR.Namespace,
			Labels:      modelContainerMeta.k8sLabels,
			Annotations: modelContainerMeta.k8sAnnotations,
		},
		Spec: appsv1.DeploymentSpec{
			Selector: &metav1.LabelSelector{
				MatchLabels: modelContainerMeta.k8sLabels,
			},
			Replicas: modelDeploymentCR.Spec.Replicas,
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels:      modelContainerMeta.k8sLabels,
					Annotations: modelContainerMeta.k8sAnnotations,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:      modelContainerName,
							Image:     modelDeploymentCR.Spec.Image,
							Resources: *modelDeploymentCR.Spec.Resources,
							Ports: []corev1.ContainerPort{
								{
									Name:          defaultModelPortName,
									ContainerPort: int32(defaultModelPort),
									Protocol:      corev1.ProtocolTCP,
								},
							},
							LivenessProbe: &corev1.Probe{
								Handler: corev1.Handler{
									HTTPGet: httpGetAction,
								},
								FailureThreshold:    defaultLivenessFailureThreshold,
								InitialDelaySeconds: *modelDeploymentCR.Spec.LivenessProbeInitialDelay,
								PeriodSeconds:       defaultLivenessPeriod,
								TimeoutSeconds:      defaultLivenessTimeout,
							},
							ReadinessProbe: &corev1.Probe{
								Handler: corev1.Handler{
									HTTPGet: httpGetAction,
								},
								FailureThreshold:    defaultReadinessFailureThreshold,
								InitialDelaySeconds: *modelDeploymentCR.Spec.ReadinessProbeInitialDelay,
								PeriodSeconds:       defaultReadinessPeriod,
								TimeoutSeconds:      defaultReadinessTimeout,
							},
						},
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, modelDeployment, r.scheme); err != nil {
		return err
	}

	found := &appsv1.Deployment{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: modelDeployment.Name, Namespace: modelDeployment.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s deployment", modelDeployment.ObjectMeta.Name))
		err = r.Create(context.TODO(), modelDeployment)
		return err
	} else if err != nil {
		return err
	}

	if !reflect.DeepEqual(modelDeployment.Spec, found.Spec) {
		found.Spec = modelDeployment.Spec
		log.Info(fmt.Sprintf("Updating %s k8s deployment", modelDeployment.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	}

	return nil
}

// Reconcile reads that state of the cluster for a ModelDeployment object and makes changes based on the state read
// and what is in the ModelDeployment.Spec
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps,resources=deployments/status,verbs=get;update;patch
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeldeployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeldeployments/status,verbs=get;update;patch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelDeployment) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ModelDeployment modelDeploymentCR
	modelDeploymentCR := &legionv1alpha1.ModelDeployment{}
	err := r.Get(context.TODO(), request.NamespacedName, modelDeploymentCR)
	if err != nil {
		if errors.IsNotFound(err) {
			// Object not found, return.  Created objects are automatically garbage collected.
			// For additional cleanup logic use finalizers.
			return reconcile.Result{}, nil
		}
		// Error reading the object - requeue the request.
		return reconcile.Result{}, err
	}

	labels, err := r.labelExtractor(modelDeploymentCR.Spec.Image)
	if err != nil {
		errorMessage := fmt.Sprintf("Label extraction from %s image is failed", modelDeploymentCR.Spec.Image)
		log.Error(err, errorMessage)

		modelDeploymentCR.Status.State = legionv1alpha1.ModelDeploymentFailed
		modelDeploymentCR.Status.Message = errorMessage

		r.recorder.Event(modelDeploymentCR,
			"Normal", string(legionv1alpha1.ModelDeploymentFailed),
			fmt.Sprintf("Exception: %s. Reason: %s", errorMessage, err.Error()),
		)

		err := r.Update(context.TODO(), modelDeploymentCR)
		if err != nil {
			log.Error(err, fmt.Sprintf("Update status of %s model deployment custom resource", modelDeploymentCR.Name))
			return reconcile.Result{}, err
		}

		return reconcile.Result{}, nil
	}

	modelId := labels[legion.DomainModelId]
	modelVersion := labels[legion.DomainModelVersion]

	if modelId == "" || modelVersion == "" {
		errorMessage := fmt.Sprintf(
			"Model docker labels for %s model image are missed: [%s, %s]",
			modelDeploymentCR.Spec.Image,
			legion.DomainModelId,
			legion.DomainModelVersion,
		)
		log.Error(err, errorMessage)

		modelDeploymentCR.Status.State = legionv1alpha1.ModelDeploymentFailed
		modelDeploymentCR.Status.Message = errorMessage

		r.recorder.Event(modelDeploymentCR,
			"Normal", string(legionv1alpha1.ModelDeploymentFailed),
			fmt.Sprintf("Exception: %s. Reason: %s", errorMessage, err.Error()),
		)

		err := r.Update(context.TODO(), modelDeploymentCR)
		if err != nil {
			log.Error(err, fmt.Sprintf("Update status of %s model deployment custom resource", modelDeploymentCR.Name))
			return reconcile.Result{}, err
		}

		return reconcile.Result{}, nil
	}

	for k, v := range modelDeploymentCR.Spec.Annotations {
		labels[k] = v
	}

	modelContainerMeta := modelContainerMetaInformation{
		modelId:      modelId,
		modelVersion: modelVersion,
		k8sName:      legion.ConvertTok8sName(modelId, modelVersion),
		k8sLabels: map[string]string{
			legion.ComponentLabel:     legion.ComponentNameModel,
			legion.SystemLabel:        legion.SystemValue,
			legion.DomainModelId:      modelId,
			legion.DomainModelVersion: modelVersion,
		},
		k8sAnnotations: labels,
	}

	err = r.reconcileDeployment(&modelContainerMeta, modelDeploymentCR)
	if err != nil {
		log.Error(err, "Reconcile k8s deployment")
		return reconcile.Result{}, err
	}

	err = r.reconcileService(&modelContainerMeta, modelDeploymentCR)
	if err != nil {
		log.Error(err, "Reconcile k8s service")
		return reconcile.Result{}, err
	}

	statusMessage := "Deployment and service were created"
	modelDeploymentCR.Status.Message = statusMessage
	// TODO: Consider using of deployment states
	modelDeploymentCR.Status.State = legionv1alpha1.ModelDeploymentCreated
	modelDeploymentCR.Status.Deployment = modelContainerMeta.k8sName
	modelDeploymentCR.Status.Service = modelContainerMeta.k8sName
	// TODO: add model edge url
	// TODO: add model id and version
	modelDeploymentCR.Status.ServiceURL = fmt.Sprintf(
		"http://%s.%s.svc.cluster.local:%d", modelContainerMeta.k8sName, modelDeploymentCR.Namespace, defaultModelPort,
	)

	if modelDeploymentCR.ObjectMeta.Labels == nil {
		modelDeploymentCR.ObjectMeta.Labels = map[string]string{}
	}

	for k, v := range modelContainerMeta.k8sLabels {
		modelDeploymentCR.ObjectMeta.Labels[k] = v
	}

	err = r.Update(context.TODO(), modelDeploymentCR)
	if err != nil {
		log.Error(err, fmt.Sprintf("Update status of %s model deployment custom resource", modelDeploymentCR.Name))
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
