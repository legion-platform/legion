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
	"github.com/knative/serving/pkg/apis/serving"
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	"github.com/spf13/viper"
	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/selection"
	"k8s.io/apimachinery/pkg/util/intstr"
	"strconv"
	"time"

	"fmt"
	authv1alpha1 "github.com/aspenmesh/istio-client-go/pkg/apis/authentication/v1alpha1"
	knservingv1alpha1 "github.com/knative/serving/pkg/apis/serving/v1alpha1"
	md_config "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	authv1alpha1_istio "istio.io/api/authentication/v1alpha1"

	"github.com/knative/serving/pkg/apis/serving/v1beta1"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
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

const (
	controllerName                       = "modeldeployment_controller"
	defaultModelPort                     = int32(5000)
	defaultLivenessFailureThreshold      = 15
	defaultLivenessPeriod                = 1
	defaultLivenessTimeout               = 1
	defaultReadinessFailureThreshold     = 15
	defaultReadinessPeriod               = 1
	defaultReadinessTimeout              = 1
	defaultRequeueDelay                  = 10 * time.Second
	defaultPortName                      = "http1"
	knativeMinReplicasKey                = "autoscaling.knative.dev/minScale"
	knativeMaxReplicasKey                = "autoscaling.knative.dev/maxScale"
	knativeAutoscalingTargetKey          = "autoscaling.knative.dev/target"
	knativeAutoscalingTargetDefaultValue = "10"
	knativeAutoscalingClass              = "autoscaling.knative.dev/class"
	knativeAutoscalingMetric             = "autoscaling.knative.dev/metric"
	defaultKnativeAutoscalingMetric      = "concurrency"
	defaultKnativeAutoscalingClass       = "kpa.autoscaling.knative.dev"
	modelNameAnnotationKey               = "modelName"
	latestReadyRevisionKey               = "latestReadyRevision"
	defaultTargetName                    = "model"
	includedAuthPrefixPath               = "/api/model/invoke"
)

var (
	log                      = logf.Log.WithName(controllerName)
	defaultWeight            = int32(100)
	defaultTerminationPeriod = int64(15)
)

func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return newConfigurableReconciler(mgr)
}

func newConfigurableReconciler(mgr manager.Manager) reconcile.Reconciler {
	return &ReconcileModelDeployment{
		Client:   mgr.GetClient(),
		scheme:   mgr.GetScheme(),
		recorder: mgr.GetRecorder(controllerName),
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

	err = c.Watch(&source.Kind{Type: &knservingv1alpha1.Configuration{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelDeployment{},
	})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &legionv1alpha1.ModelRoute{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelDeployment{},
	})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &appsv1.Deployment{}}, &EnqueueRequestForImplicitOwner{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &knservingv1alpha1.Revision{}}, &EnqueueRequestForImplicitOwner{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Endpoints{}}, &EnqueueRequestForImplicitOwner{})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelDeployment{}

// ReconcileModelDeployment reconciles a ModelDeployment object
type ReconcileModelDeployment struct {
	client.Client
	scheme   *runtime.Scheme
	recorder record.EventRecorder
}

func knativeConfigurationName(md *legionv1alpha1.ModelDeployment) string {
	return md.Name
}

func knativeDeploymentName(revisionName string) string {
	return fmt.Sprintf("%s-deployment", revisionName)
}

func modelRouteName(md *legionv1alpha1.ModelDeployment) string {
	return md.Name
}

func (r *ReconcileModelDeployment) ReconcileModelRoute(modelDeploymentCR *legionv1alpha1.ModelDeployment,
	latestReadyRevision string) error {
	modelRoute := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      modelRouteName(modelDeploymentCR),
			Namespace: modelDeploymentCR.Namespace,
			Annotations: map[string]string{
				legionv1alpha1.SkipUrlValidationKey: legionv1alpha1.SkipUrlValidationValue,
				latestReadyRevisionKey:              latestReadyRevision,
			},
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix: fmt.Sprintf("/model/%s", modelDeploymentCR.Name),
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   modelDeploymentCR.Name,
					Weight: &defaultWeight,
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, modelRoute, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(modelRoute); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &legionv1alpha1.ModelRoute{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: modelRoute.Name, Namespace: modelRoute.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s model route", modelRoute.ObjectMeta.Name))
		err = r.Create(context.TODO(), modelRoute)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(modelRoute, found) {
		log.Info(fmt.Sprintf("Model Route hashes don't equal. Update the %s Model route", modelRoute.Name))

		found.Spec = modelRoute.Spec
		found.ObjectMeta.Annotations = modelRoute.ObjectMeta.Annotations
		found.ObjectMeta.Labels = modelRoute.ObjectMeta.Labels

		log.Info(fmt.Sprintf("Updating %s k8s model route", modelRoute.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf("Model Route hashes equal. Skip updating of the %s model route", modelRoute.Name))
	}

	return nil
}

func (r *ReconcileModelDeployment) ReconcileKnativeConfiguration(modelDeploymentCR *legionv1alpha1.ModelDeployment) error {
	container, err := r.createModelContainer(modelDeploymentCR)
	if err != nil {
		return err
	}

	knativeConfiguration := &knservingv1alpha1.Configuration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      knativeConfigurationName(modelDeploymentCR),
			Namespace: modelDeploymentCR.Namespace,
		},
		Spec: knservingv1alpha1.ConfigurationSpec{
			Template: &knservingv1alpha1.RevisionTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						modelNameAnnotationKey: modelDeploymentCR.Name,
					},
					Annotations: map[string]string{
						knativeAutoscalingClass:     defaultKnativeAutoscalingClass,
						knativeAutoscalingMetric:    defaultKnativeAutoscalingMetric,
						knativeMinReplicasKey:       strconv.Itoa(int(*modelDeploymentCR.Spec.MinReplicas)),
						knativeMaxReplicasKey:       strconv.Itoa(int(*modelDeploymentCR.Spec.MaxReplicas)),
						knativeAutoscalingTargetKey: knativeAutoscalingTargetDefaultValue,
					},
				},
				Spec: knservingv1alpha1.RevisionSpec{
					RevisionSpec: v1beta1.RevisionSpec{
						TimeoutSeconds: &defaultTerminationPeriod,
						PodSpec: v1beta1.PodSpec{
							ServiceAccountName: "regsecret",
							Containers: []corev1.Container{
								*container,
							},
						},
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, knativeConfiguration, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHashKnative(knativeConfiguration); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &knservingv1alpha1.Configuration{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name: knativeConfiguration.Name, Namespace: knativeConfiguration.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s Knative Configuration", knativeConfiguration.ObjectMeta.Name))
		err = r.Create(context.TODO(), knativeConfiguration)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(knativeConfiguration, found) {
		log.Info(fmt.Sprintf("Knative Configuration hashes don't equal. Update the %s Knative Configuration", knativeConfiguration.Name))

		found.Spec = knativeConfiguration.Spec
		found.ObjectMeta.Annotations = knativeConfiguration.ObjectMeta.Annotations
		found.ObjectMeta.Labels = knativeConfiguration.ObjectMeta.Labels

		log.Info(fmt.Sprintf("Updating %s Knative Configuration", knativeConfiguration.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf("Knative Configuration hashes equal. Skip updating of the %s Knative Configuration", knativeConfiguration.Name))
	}

	return nil
}

func (r *ReconcileModelDeployment) createModelContainer(modelDeploymentCR *legionv1alpha1.ModelDeployment) (*corev1.Container, error) {
	httpGetAction := &corev1.HTTPGetAction{
		Path: "/healthcheck",
	}

	depResources, err := kubernetes.ConvertLegionResourcesToK8s(modelDeploymentCR.Spec.Resources)
	if err != nil {
		return nil, err
	}

	return &corev1.Container{
		Image:     modelDeploymentCR.Spec.Image,
		Resources: depResources,
		Ports: []corev1.ContainerPort{
			{
				Name:          defaultPortName,
				ContainerPort: defaultModelPort,
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
	}, nil
}

// Reconcile the Istio Policy for model authorization
// Read more about in Istio docs https://istio.io/docs/tasks/security/rbac-groups/#configure-json-web-token-jwt-authentication-with-mutual-tls
// Configuration https://istio.io/docs/reference/config/istio.authentication.v1alpha1/
func (r *ReconcileModelDeployment) reconcileAuthPolicy(modelDeploymentCR *legionv1alpha1.ModelDeployment) error {
	envoyAuthFilter := &authv1alpha1.Policy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      modelDeploymentCR.Name,
			Namespace: modelDeploymentCR.Namespace,
		},
		Spec: authv1alpha1.PolicySpec{
			Policy: authv1alpha1_istio.Policy{
				Targets: []*authv1alpha1_istio.TargetSelector{
					{
						// The value does not matter.
						Name: defaultTargetName,
						Labels: map[string]string{
							// We assign the same labels for our model deployments
							modelNameAnnotationKey: modelDeploymentCR.Name,
						},
					},
				},
				Origins: []*authv1alpha1_istio.OriginAuthenticationMethod{
					{
						Jwt: &authv1alpha1_istio.Jwt{
							Issuer:  viper.GetString(md_config.SecurityJwksIssuer),
							JwksUri: viper.GetString(md_config.SecurityJwksUrl),
							TriggerRules: []*authv1alpha1_istio.Jwt_TriggerRule{
								{
									// Healthcheck paths must be ignored
									IncludedPaths: []*authv1alpha1_istio.StringMatch{
										{
											MatchType: &authv1alpha1_istio.StringMatch_Prefix{
												Prefix: includedAuthPrefixPath,
											},
										},
									},
								},
							},
						},
					},
				},
				PrincipalBinding: authv1alpha1_istio.PrincipalBinding_USE_ORIGIN,
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, envoyAuthFilter, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(envoyAuthFilter); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &authv1alpha1.Policy{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: envoyAuthFilter.Name, Namespace: envoyAuthFilter.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s Istio Auth Policy", envoyAuthFilter.ObjectMeta.Name))

		return r.Create(context.TODO(), envoyAuthFilter)
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(envoyAuthFilter, found) {
		log.Info(fmt.Sprintf("Istio Auth Policy hashes don't equal. Update the %s Model route", envoyAuthFilter.Name))

		found.Spec = envoyAuthFilter.Spec
		found.ObjectMeta.Annotations = envoyAuthFilter.ObjectMeta.Annotations
		found.ObjectMeta.Labels = envoyAuthFilter.ObjectMeta.Labels

		log.Info(fmt.Sprintf("Updating %s k8s Istio Auth Policy", envoyAuthFilter.ObjectMeta.Name))

		if err := r.Update(context.TODO(), found); err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf("Istio Auth Policy hashes equal. Skip updating of the %s Istio Auth Policy", envoyAuthFilter.Name))
	}

	return nil
}

// Retrieve current configuration and return last revision name.
// If the latest revision name equals the latest created revision, then last deployment changes were applied.
func (r *ReconcileModelDeployment) getLatestReadyRevision(modelDeploymentCR *legionv1alpha1.ModelDeployment) (string, bool, error) {
	knativeConfiguration := &knservingv1alpha1.Configuration{}
	if err := r.Get(context.TODO(), types.NamespacedName{
		Name: knativeConfigurationName(modelDeploymentCR), Namespace: modelDeploymentCR.Namespace,
	}, knativeConfiguration); errors.IsNotFound(err) {
		return "", false, nil
	} else if err != nil {
		log.Error(err, "Getting Knative Configuration")
		return "", false, err
	}

	latestReadyRevisionName := knativeConfiguration.Status.LatestReadyRevisionName
	return latestReadyRevisionName,
		len(latestReadyRevisionName) != 0 && latestReadyRevisionName == knativeConfiguration.Status.LatestCreatedRevisionName,
		nil
}

func (r *ReconcileModelDeployment) reconcileStatus(modelDeploymentCR *legionv1alpha1.ModelDeployment,
	state legionv1alpha1.ModelDeploymentState, latestReadyRevision string) error {

	modelDeploymentCR.Status.State = state

	if len(latestReadyRevision) != 0 {
		modelDeploymentCR.Status.ServiceURL = fmt.Sprintf(
			"%s.%s.svc.cluster.local", modelDeploymentCR.Name, modelDeploymentCR.Namespace,
		)
		modelDeploymentCR.Status.LastRevisionName = latestReadyRevision
	}

	if err := r.Update(context.TODO(), modelDeploymentCR); err != nil {
		log.Error(err, fmt.Sprintf("Update status of %s model deployment custom resource", modelDeploymentCR.Name))
		return err
	}

	return nil
}

// Reconciles a separate kubernetes service for a model deployment with stable name
func (r *ReconcileModelDeployment) reconcileService(modelDeploymentCR *legionv1alpha1.ModelDeployment) error {
	service := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      modelDeploymentCR.Name,
			Namespace: modelDeploymentCR.Namespace,
		},
		Spec: corev1.ServiceSpec{
			Ports: []corev1.ServicePort{
				{
					Name:       "http",
					Protocol:   corev1.ProtocolTCP,
					Port:       80,
					TargetPort: intstr.FromInt(8012),
				},
			},
			Type: corev1.ServiceTypeClusterIP,
		},
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, service, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(service); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.Service{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: service.Name, Namespace: service.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s service", service.ObjectMeta.Name))
		err = r.Create(context.TODO(), service)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(service, found) {
		log.Info(fmt.Sprintf("service hashes don't equal. Update the %s service", service.Name))

		// ClusterIP must not change
		clusterIp := found.Spec.ClusterIP
		found.Spec = service.Spec
		found.Spec.ClusterIP = clusterIp

		log.Info(fmt.Sprintf("Updating %s k8s service", service.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf("k8s service hashes equal. Skip updating of the %s service", service.Name))
	}

	if err := r.reconcileEndpoints(modelDeploymentCR); err != nil {
		log.Error(err, "Can not reconcile endpoints", "model deployment id", modelDeploymentCR.Name)
	}

	return nil
}

// Syncs subsets endpoints of a model deployment service with subsets endpoints of the latest model knative revision
func (r *ReconcileModelDeployment) reconcileEndpoints(modelDeploymentCR *legionv1alpha1.ModelDeployment) error {
	lastRevisionName := modelDeploymentCR.Status.LastRevisionName
	if len(lastRevisionName) == 0 {
		log.Info("Last revision name is empty", "model deployment id", modelDeploymentCR.Name)

		return nil
	}

	knativeEndpoints := &corev1.Endpoints{}

	if err := r.Get(context.TODO(), types.NamespacedName{
		Namespace: modelDeploymentCR.Namespace,
		Name:      lastRevisionName,
	}, knativeEndpoints); err != nil {
		log.Error(err, "Can not get the knative endpoints endpoints",
			"model deployment id", modelDeploymentCR.Name,
			"last revision name", lastRevisionName)

		return err
	}

	endpoints := &corev1.Endpoints{
		ObjectMeta: metav1.ObjectMeta{
			Name:      modelDeploymentCR.Name,
			Namespace: modelDeploymentCR.Namespace,
		},
		Subsets: knativeEndpoints.Subsets,
	}

	if err := controllerutil.SetControllerReference(modelDeploymentCR, endpoints, r.scheme); err != nil {
		return err
	}

	if err := legion.StoreHash(endpoints); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return err
	}

	found := &corev1.Endpoints{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: endpoints.Name, Namespace: endpoints.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s endpoints", endpoints.ObjectMeta.Name))
		err = r.Create(context.TODO(), endpoints)
		return err
	} else if err != nil {
		return err
	}

	if !legion.ObjsEqualByHash(endpoints, found) {
		log.Info(fmt.Sprintf("endpoints hashes don't equal. Update the %s endpoints", endpoints.Name))

		found.Subsets = endpoints.Subsets

		log.Info(fmt.Sprintf("Updating %s k8s endpoints", endpoints.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return err
		}
	} else {
		log.Info(fmt.Sprintf("k8s endpoints hashes equal. Skip updating of the %s endpoints", endpoints.Name))
	}

	return nil
}

// Cleanup old Knative revisions
// Workaround for https://github.com/knative/serving/issues/2720
// TODO: need to upgrade knative
func (r *ReconcileModelDeployment) cleanupOldRevisions(modelDeploymentCR *legionv1alpha1.ModelDeployment) error {
	lastRevisionName := modelDeploymentCR.Status.LastRevisionName
	if len(lastRevisionName) == 0 {
		log.Info("Last revision name is empty", "model deployment id", modelDeploymentCR.Name)

		return nil
	}

	lastKnativeRevision := &knservingv1alpha1.Revision{}
	if err := r.Get(context.TODO(), types.NamespacedName{
		Name: lastRevisionName, Namespace: modelDeploymentCR.Namespace,
	}, lastKnativeRevision); err != nil {
		log.Error(err, "Getting Knative Revision", "model deployment id", modelDeploymentCR.Name)

		return err
	}

	lastKnativeRevisionGenerationStr, ok := lastKnativeRevision.Labels[serving.ConfigurationGenerationLabelKey]
	if !ok {
		return fmt.Errorf("can not get the lastest knative revision generation: %s", lastKnativeRevisionGenerationStr)
	}

	lastKnativeRevisionGeneration, err := strconv.Atoi(lastKnativeRevisionGenerationStr)
	if err != nil {
		return err
	}

	knativeRevisions := &knservingv1alpha1.RevisionList{}

	labelSelectorReq, err := labels.NewRequirement(modelNameAnnotationKey, selection.DoubleEquals, []string{modelDeploymentCR.Name})
	if err != nil {
		log.Error(err, "Creation of the label selector requirement", "model deployment id", modelDeploymentCR.Name)
		return err
	}

	labelSelector := labels.NewSelector()
	labelSelector.Add(*labelSelectorReq)

	if err := r.List(context.TODO(), &client.ListOptions{
		LabelSelector: labelSelector,
		Namespace:     modelDeploymentCR.Namespace,
	}, knativeRevisions); err != nil {
		log.Error(err, "Get the list of knative revisions", "model deployment id", modelDeploymentCR.Name)

		return err
	}

	for _, kr := range knativeRevisions.Items {
		modelDeploymentName, ok := kr.Labels[modelNameAnnotationKey]
		if !ok || modelDeploymentName != modelDeploymentCR.Name {
			continue
		}

		krGenerationStr, ok := kr.Labels[serving.ConfigurationGenerationLabelKey]
		if !ok {
			return fmt.Errorf("can not get the lastest knative revision generation: %s", kr.Name)
		}

		krGeneration, err := strconv.Atoi(krGenerationStr)
		if err != nil {
			return err
		}

		if krGeneration < lastKnativeRevisionGeneration {
			if err := r.Delete(context.TODO(), &kr); err != nil {
				log.Error(err, "Delete old knative revision",
					"model deployment id", modelDeploymentCR.Name,
					"knative revision name", kr.Name,
					"knative revision generation", krGeneration)
				return err
			}

			log.Info("Delete old knative revision",
				"model deployment id", modelDeploymentCR.Name,
				"knative revision name", kr.Name,
				"knative revision generation", krGeneration)
		}
	}

	return nil
}

// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps,resources=deployments/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=endpoints,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=endpoints/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=authentication.istio.io,resources=policies,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=authentication.istio.io,resources=policies/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeldeployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modeldeployments/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=serving.knative.dev,resources=configurations,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=serving.knative.dev,resources=revisions,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=serving.knative.dev,resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=serving.knative.dev,resources=routes,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.internal.knative.dev,resources=certificates,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.internal.knative.dev,resources=serverlessservices,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.internal.knative.dev,resources=clusteringresses,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=caching.internal.knative.dev,resources=images,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=autoscaling.internal.knative.dev,resources=podautoscalers,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.istio.io,resources=envoyfilters,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
func (r *ReconcileModelDeployment) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ModelDeployment modelDeploymentCR
	modelDeploymentCR := &legionv1alpha1.ModelDeployment{}
	err := r.Get(context.TODO(), request.NamespacedName, modelDeploymentCR)
	if err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}

		return reconcile.Result{}, err
	}

	for _, finalizer := range modelDeploymentCR.ObjectMeta.Finalizers {
		if finalizer == metav1.FinalizerDeleteDependents {
			log.Info(fmt.Sprintf("Found %s finalizer. Skip reconciling", metav1.FinalizerDeleteDependents),
				"Model Deployment name", modelDeploymentCR.Name)

			if err := r.reconcileStatus(modelDeploymentCR, legionv1alpha1.ModelDeploymentStateDeleting, ""); err != nil {
				log.Error(err, "Set deleting deployment state")
				return reconcile.Result{}, err
			}

			return reconcile.Result{}, nil
		}
	}

	log.Info("Start reconciling of model deployment", "Name", modelDeploymentCR.Name)

	if viper.GetBool(md_config.SecurityJwksEnabled) {
		log.Info("Reconcile Auth Filter", "Model Deployment name", modelDeploymentCR.Name)

		if err := r.reconcileAuthPolicy(modelDeploymentCR); err != nil {
			log.Error(err, "Reconcile Istio Auth Policy")
			return reconcile.Result{}, err
		}
	}

	if err := r.ReconcileKnativeConfiguration(modelDeploymentCR); err != nil {
		log.Error(err, "Reconcile Knative Configuration")
		return reconcile.Result{}, err
	}

	latestReadyRevision, configurationReady, err := r.getLatestReadyRevision(modelDeploymentCR)
	if err != nil {
		log.Error(err, "Getting latest revision", "Model Deployment name", modelDeploymentCR.Name)
		return reconcile.Result{}, err
	}

	if !configurationReady {
		log.Info("Configuration was not updated yet. Put the Model Deployment back in the queue", "Model Deployment name", modelDeploymentCR.Name)

		_ = r.reconcileStatus(modelDeploymentCR, legionv1alpha1.ModelDeploymentStateProcessing, "")

		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	}

	log.Info("Reconcile default Model Route", "Model Deployment name", modelDeploymentCR.Name)

	if err := r.ReconcileModelRoute(modelDeploymentCR, latestReadyRevision); err != nil {
		log.Error(err, "Reconcile the default Model Route")
		return reconcile.Result{}, err
	}

	if err := r.reconcileService(modelDeploymentCR); err != nil {
		log.Error(err, "Reconcile the k8s service")
		return reconcile.Result{}, err
	}

	modelDeployment := &appsv1.Deployment{}
	modelDeploymentKey := types.NamespacedName{
		Name:      knativeDeploymentName(latestReadyRevision),
		Namespace: viper.GetString(md_config.Namespace),
	}

	if err := r.Client.Get(context.TODO(), modelDeploymentKey, modelDeployment); errors.IsNotFound(err) {
		_ = r.reconcileStatus(modelDeploymentCR, legionv1alpha1.ModelDeploymentStateProcessing, latestReadyRevision)

		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	} else if err != nil {
		log.Error(err, "Getting of model deployment", "Model Deployment name", modelDeploymentCR.Name,
			"K8s Deployment name", modelDeploymentKey.Name)

		return reconcile.Result{}, err
	}

	modelDeploymentCR.Status.Replicas = modelDeployment.Status.Replicas
	modelDeploymentCR.Status.AvailableReplicas = modelDeployment.Status.AvailableReplicas
	modelDeploymentCR.Status.Deployment = modelDeployment.Name

	if modelDeploymentCR.Status.Replicas != modelDeploymentCR.Status.AvailableReplicas {
		_ = r.reconcileStatus(modelDeploymentCR, legionv1alpha1.ModelDeploymentStateProcessing, latestReadyRevision)

		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	}

	if err := r.reconcileStatus(modelDeploymentCR, legionv1alpha1.ModelDeploymentStateReady, latestReadyRevision); err != nil {
		log.Error(err, "Reconcile Model Deployment Status", "Model Deployment name", modelDeploymentCR.Name)
		return reconcile.Result{}, err
	}

	if err := r.cleanupOldRevisions(modelDeploymentCR); err != nil {
		log.Error(err, "Cleanup old revisions", "model_deployment_id", modelDeploymentCR.Name)
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
