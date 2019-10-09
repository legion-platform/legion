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
	"encoding/base64"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	train_conf "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/trainer"
	"github.com/spf13/viper"
	"reflect"

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

var log = logf.Log.WithName("controller")

func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

type PublicKeyEvaluator func(string) (string, error)

func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return newConfigurableReconciler(mgr, EvaluatePublicKey)
}

func newConfigurableReconciler(mgr manager.Manager, keyEvaluator PublicKeyEvaluator) reconcile.Reconciler {
	return &ReconcileConnection{Client: mgr.GetClient(), scheme: mgr.GetScheme(), keyEvaluator: keyEvaluator}
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
}

// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=connections,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=legion.legion-platform.org,resources=connections/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=core,resources=secrets,verbs=get;list;watch;create;update;patch;delete
func (r *ReconcileConnection) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	// Fetch the ConnectionName connectionCR
	connectionCR := &legionv1alpha1.Connection{}
	err := r.Get(context.TODO(), request.NamespacedName, connectionCR)
	if err != nil {
		if errors.IsNotFound(err) {
			// Object not found, return.  Created objects are automatically garbage collected.
			// For additional cleanup logic use finalizers.
			return reconcile.Result{}, nil
		}
		// Error reading the object - requeue the request.
		return reconcile.Result{}, err
	}

	if connectionCR.Spec.Type != connection.GITType {
		return reconcile.Result{}, nil
	}

	decodedRsa, err := base64.StdEncoding.DecodeString(connectionCR.Spec.KeySecret)
	if err != nil {
		log.Error(err, fmt.Sprintf("Can't decode %s vcs ssh key", connectionCR.Name))

		return reconcile.Result{}, nil
	}

	rawPublicKey := connectionCR.Spec.PublicKey
	var publicKey []byte
	if rawPublicKey == "" {
		log.Info("Public key is empty. Extract from vcs url")

		rawPublicKey, err = r.keyEvaluator(connectionCR.Spec.URI)
		if err != nil {
			return reconcile.Result{}, err
		}

		publicKey = []byte(rawPublicKey)
	} else {
		publicKey, err = base64.StdEncoding.DecodeString(rawPublicKey)
		if err != nil {
			log.Error(err, "Can't decode % vcs public key", rawPublicKey)
			return reconcile.Result{}, nil
		}
	}

	vcsSecretName := legion.GenerateConnectionSecretName(connectionCR.Name)
	expectedSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsSecretName,
			Namespace: viper.GetString(train_conf.Namespace),
		},
		Data: map[string][]byte{
			trainer.GitSSHKeyFileName: decodedRsa,
			PublicSSHKeyName:          publicKey,
		},
	}

	var foundSecret = &corev1.Secret{}
	secretNamespacedName := types.NamespacedName{Name: vcsSecretName, Namespace: viper.GetString(train_conf.Namespace)}
	if err := r.Get(context.TODO(), secretNamespacedName, foundSecret); err != nil && errors.IsNotFound(err) {
		err = r.Create(context.TODO(), expectedSecret)
		if err != nil {
			// If error during secret creation
			log.Error(err, "Kubernetes secret creation")
			return reconcile.Result{}, err
		}

		log.Info(fmt.Sprintf("Created %s vcs secret", expectedSecret.Name))

		return reconcile.Result{}, nil
	} else if err != nil {
		log.Error(err, "Fetching Secret")
		return reconcile.Result{}, err
	}

	if !reflect.DeepEqual(foundSecret.Data, expectedSecret.Data) {
		foundSecret.Data = expectedSecret.Data

		log.Info("Updating Secret")
		err = r.Update(context.TODO(), foundSecret)
		if err != nil {
			return reconcile.Result{}, err
		}
	}

	return reconcile.Result{}, nil
}
