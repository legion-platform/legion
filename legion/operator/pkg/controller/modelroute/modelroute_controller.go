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

package modelroute

import (
	"context"
	"fmt"
	v1alpha3_istio_api "github.com/aspenmesh/istio-client-go/pkg/apis/networking/v1alpha3"
	gogotypes "github.com/gogo/protobuf/types"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	md_config "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	v1alpha3_istio "istio.io/api/networking/v1alpha3"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"time"

	"k8s.io/apimachinery/pkg/api/errors"
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
	knativeRevisionHeader    = "knative-serving-revision"
	knativeNamespaceHeader   = "knative-serving-namespace"
	defaultRetryAttempts     = 30
	defaultListOfRetryCauses = "5xx,connect-failure,refused-stream"
)

var (
	log                  = logf.Log.WithName("model_route_controller")
	defaultTimeoutPerTry = gogotypes.DurationProto(time.Second)
	defaultRequeueDelay  = 1 * time.Second
)

func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return &ReconcileModelRoute{Client: mgr.GetClient(), scheme: mgr.GetScheme()}
}

func add(mgr manager.Manager, r reconcile.Reconciler) error {
	c, err := controller.New("modelroute-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &legionv1alpha1.ModelRoute{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &v1alpha3_istio_api.VirtualService{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.ModelRoute{},
	})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelRoute{}

type ReconcileModelRoute struct {
	client.Client
	scheme *runtime.Scheme
}

func VirtualServiceName(mr *legionv1alpha1.ModelRoute) string {
	return mr.Name
}

func (r *ReconcileModelRoute) reconcileVirtualService(modelRouteCR *legionv1alpha1.ModelRoute) (bool, error) {
	httpTargets := []*v1alpha3_istio.HTTPRouteDestination{}
	reconileAgain := false

	for _, md := range modelRouteCR.Spec.ModelDeploymentTargets {
		modelDeployment := &legionv1alpha1.ModelDeployment{}
		if err := r.Get(context.TODO(), types.NamespacedName{
			Name: md.Name, Namespace: modelRouteCR.Namespace,
		}, modelDeployment); errors.IsNotFound(err) {
			log.Error(
				err, "Model Deployment is not found",
				"Model Deployment Name", md.Name,
				"Model Route Name", modelRouteCR.Name,
			)

			reconileAgain = true
			continue
		} else if err != nil {
			log.Error(
				err, "Getting of the Model Deployment",
				"Model Deployment Name", md.Name,
				"Model Route Name", modelRouteCR.Name,
			)

			return reconileAgain, err
		}

		if modelDeployment.Status.State != legionv1alpha1.ModelDeploymentStateReady {
			log.Info("Model deployment is not ready", "Model Deployment Name", md.Name, "Model Route Name", modelRouteCR.Name)
			reconileAgain = true

			continue
		}

		httpTargets = append(httpTargets,
			&v1alpha3_istio.HTTPRouteDestination{
				Destination: &v1alpha3_istio.Destination{
					Host: modelDeployment.Status.ServiceURL,
					Port: &v1alpha3_istio.PortSelector{
						Port: &v1alpha3_istio.PortSelector_Number{
							Number: uint32(80),
						},
					},
				},
				Weight: *md.Weight,
				Headers: &v1alpha3_istio.Headers{
					Request: &v1alpha3_istio.Headers_HeaderOperations{
						Add: map[string]string{
							knativeRevisionHeader:  modelDeployment.Status.LastRevisionName,
							knativeNamespaceHeader: viper.GetString(md_config.Namespace),
						},
					},
				},
			})
	}

	if len(httpTargets) == 0 {
		log.Info("Number of http targets is zero", "Model Route Name", modelRouteCR.Name)
		return reconileAgain, nil
	}

	var mirror *v1alpha3_istio.Destination
	if modelRouteCR.Spec.Mirror != nil && len(*modelRouteCR.Spec.Mirror) != 0 {
		modelDeployment := &legionv1alpha1.ModelDeployment{}
		if err := r.Get(context.TODO(), types.NamespacedName{
			Name: *modelRouteCR.Spec.Mirror, Namespace: modelRouteCR.Namespace,
		}, modelDeployment); errors.IsNotFound(err) {

		} else if err != nil {
			log.Error(err, fmt.Sprintf("Getting of %s Model Deployment mirror", *modelRouteCR.Spec.Mirror))

			return reconileAgain, err
		}

		if modelDeployment.Status.State != legionv1alpha1.ModelDeploymentStateReady {
			log.Info(
				"Model deployment is not ready",
				"Model Deployment Name", modelRouteCR.Spec.Mirror,
				"Model Route Name", modelRouteCR.Name,
			)

			reconileAgain = true
		} else {
			mirror = &v1alpha3_istio.Destination{
				Host: modelDeployment.Status.ServiceURL,
			}
		}
	}

	vservice := &v1alpha3_istio_api.VirtualService{
		ObjectMeta: metav1.ObjectMeta{
			Name:      VirtualServiceName(modelRouteCR),
			Namespace: modelRouteCR.Namespace,
		},
		Spec: v1alpha3_istio_api.VirtualServiceSpec{
			VirtualService: v1alpha3_istio.VirtualService{
				Hosts:    []string{"*"},
				Gateways: []string{"edge"},
				Http: []*v1alpha3_istio.HTTPRoute{
					{
						Retries: &v1alpha3_istio.HTTPRetry{
							Attempts:      defaultRetryAttempts,
							PerTryTimeout: defaultTimeoutPerTry,
							RetryOn:       defaultListOfRetryCauses,
						},
						Match: []*v1alpha3_istio.HTTPMatchRequest{
							{
								Uri: &v1alpha3_istio.StringMatch{
									MatchType: &v1alpha3_istio.StringMatch_Exact{
										Exact: modelRouteCR.Spec.URLPrefix,
									},
								},
							},
						},
						Rewrite: &v1alpha3_istio.HTTPRewrite{
							Uri: "/api/model/info",
						},
						Route:  httpTargets,
						Mirror: mirror,
					},
					{
						Retries: &v1alpha3_istio.HTTPRetry{
							Attempts:      defaultRetryAttempts,
							PerTryTimeout: defaultTimeoutPerTry,
							RetryOn:       defaultListOfRetryCauses,
						},
						Match: []*v1alpha3_istio.HTTPMatchRequest{
							{
								Uri: &v1alpha3_istio.StringMatch{
									MatchType: &v1alpha3_istio.StringMatch_Prefix{
										Prefix: fmt.Sprintf("%s/api", modelRouteCR.Spec.URLPrefix),
									},
								},
							},
						},
						Rewrite: &v1alpha3_istio.HTTPRewrite{
							Uri: "/api",
						},
						Route:  httpTargets,
						Mirror: mirror,
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(modelRouteCR, vservice, r.scheme); err != nil {
		return reconileAgain, err
	}

	if err := legion.StoreHash(vservice); err != nil {
		log.Error(err, "Cannot apply obj hash")
		return reconileAgain, err
	}

	found := &v1alpha3_istio_api.VirtualService{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name: vservice.Name, Namespace: vservice.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {
		log.Info(fmt.Sprintf("Creating %s k8s Istio Virtual Service", vservice.ObjectMeta.Name))
		err = r.Create(context.TODO(), vservice)
		return reconileAgain, err
	} else if err != nil {
		return reconileAgain, err
	}

	if !legion.ObjsEqualByHash(vservice, found) {
		log.Info(fmt.Sprintf("Istio Virtual Service hashes don't equal. Update the %s Model route", vservice.Name))

		found.Spec = vservice.Spec
		found.ObjectMeta.Annotations = vservice.ObjectMeta.Annotations
		found.ObjectMeta.Labels = vservice.ObjectMeta.Labels

		log.Info(fmt.Sprintf("Updating %s k8s Istio Virtual Service", vservice.ObjectMeta.Name))
		err = r.Update(context.TODO(), found)
		if err != nil {
			return reconileAgain, err
		}
	} else {
		log.Info(fmt.Sprintf(
			"Istio Virtual Service hashes equal. Skip updating of the %s Istio Virtual Service",
			vservice.Name),
		)
	}

	return reconileAgain, err
}

func (r *ReconcileModelRoute) reconcileStatus(modelRouteCR *legionv1alpha1.ModelRoute,
	state legionv1alpha1.ModelRouteState) error {
	modelRouteCR.Status.EdgeURL = fmt.Sprintf(
		"%s%s", viper.GetString(md_config.EdgeHost), modelRouteCR.Spec.URLPrefix,
	)
	modelRouteCR.Status.State = state

	if err := r.Update(context.TODO(), modelRouteCR); err != nil {
		log.Error(err, "Update status of model deployment custom resource", "Model Deployment Name", modelRouteCR.Name)
		return err
	}

	return nil
}

// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelroutes,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=modelroutes/status,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.istio.io,resources=virtualservices,verbs=get;list;watch;create;update;patch;delete
func (r *ReconcileModelRoute) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	modelRouteCR := &legionv1alpha1.ModelRoute{}
	err := r.Get(context.TODO(), request.NamespacedName, modelRouteCR)
	if err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}

		return reconcile.Result{}, err
	}

	if reconcileAgain, err := r.reconcileVirtualService(modelRouteCR); err != nil {
		log.Error(err, "Reconcile Istio Virtual Service")
		return reconcile.Result{}, err
	} else if reconcileAgain {
		_ = r.reconcileStatus(modelRouteCR, legionv1alpha1.ModelRouteStateProcessing)

		log.Info("Put the Model Route back in the queue", "Model Route Name", modelRouteCR.Name)
		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	}

	if err := r.reconcileStatus(modelRouteCR, legionv1alpha1.ModelRouteStateReady); err != nil {
		log.Info("Reconcile Status of Model Route", "error", err)
		return reconcile.Result{}, err
	}

	return reconcile.Result{}, nil
}
