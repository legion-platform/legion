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

package connection

import (
	"context"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	operator_conf "github.com/legion-platform/legion/legion/operator/pkg/config/operator"
	connection_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	connection_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/http"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

var log = logf.Log.WithName("controller")

func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

type PublicKeyEvaluator func(string) (string, error)

func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return newConfigurableReconciler(mgr, utils.EvaluatePublicKey)
}

func newConfigurableReconciler(mgr manager.Manager, keyEvaluator PublicKeyEvaluator) reconcile.Reconciler {
	return &ReconcileConnection{
		Client:       mgr.GetClient(),
		scheme:       mgr.GetScheme(),
		keyEvaluator: keyEvaluator,
		connRepo: connection_http_repository.NewRepository(
			viper.GetString(operator_conf.EdiURL),
			viper.GetString(operator_conf.EdiToken),
		),
	}
}

// add adds a new Controller to mgr with r as the reconcile.Reconciler
func add(mgr manager.Manager, r reconcile.Reconciler) error {
	// Create a new controller
	c, err := controller.New("connection-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &legionv1alpha1.Connection{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &corev1.Secret{}}, &handler.EnqueueRequestForOwner{
		IsController: true,
		OwnerType:    &legionv1alpha1.Connection{},
	})

	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileConnection{}

// ReconcileConnection reconciles a ConnectionName object
type ReconcileConnection struct {
	client.Client
	scheme       *runtime.Scheme
	keyEvaluator PublicKeyEvaluator
	connRepo     connection_repository.Repository
}

// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=connections,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=connections/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
func (r *ReconcileConnection) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ConnectionName connectionCR
	conn := &legionv1alpha1.Connection{}
	err := r.Get(context.TODO(), request.NamespacedName, conn)
	if err != nil {
		if errors.IsNotFound(err) {
			// Object not found, return.  Created objects are automatically garbage collected.
			// For additional cleanup logic use finalizers.
			return reconcile.Result{}, nil
		}
		// Error reading the object - requeue the request.
		return reconcile.Result{}, err
	}

	// Currently we have just log the reconcile. TODO: think about reconciliation of an ECR token
	log.Info("Finish reconcile of connection", "conn_id", conn.Name)

	return reconcile.Result{}, nil
}
