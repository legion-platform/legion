/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package modelroute

import (
	"context"
	gogotypes "github.com/gogo/protobuf/types"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog/catalog"
	"io/ioutil"
	"net/http"
	"time"

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

var (
	log                  = logf.Log.WithName("service-catalog-controller")
	defaultTimeoutPerTry = gogotypes.DurationProto(time.Second)
	defaultRequeueDelay  = 1 * time.Second
)

func Add(mgr manager.Manager, mrc *catalog.ModelRouteCatalog) error {
	return add(mgr, newReconciler(mgr, mrc))
}

func newReconciler(mgr manager.Manager, mrc *catalog.ModelRouteCatalog) reconcile.Reconciler {
	return &ReconcileModelRoute{Client: mgr.GetClient(), scheme: mgr.GetScheme(), mrc: mrc}
}

func add(mgr manager.Manager, r reconcile.Reconciler) error {
	c, err := controller.New("service-catalog-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	err = c.Watch(&source.Kind{Type: &legionv1alpha1.ModelRoute{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileModelRoute{}

type ReconcileModelRoute struct {
	client.Client
	scheme *runtime.Scheme
	mrc    *catalog.ModelRouteCatalog
}

func (r *ReconcileModelRoute) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	modelRouteCR := &legionv1alpha1.ModelRoute{}
	err := r.Get(context.TODO(), request.NamespacedName, modelRouteCR)
	if err != nil {
		if errors.IsNotFound(err) {
			r.mrc.DeleteModelRoute(modelRouteCR)

			return reconcile.Result{}, nil
		}

		return reconcile.Result{}, err
	}

	if modelRouteCR.Status.State != legionv1alpha1.ModelRouteStateReady {
		log.Info("Model is not ready", "mr id", modelRouteCR.Name)
		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	}

	response, err := http.Get(modelRouteCR.Status.EdgeUrl)
	if err != nil {
		log.Error(err, "Can not get swagger response for model", "mr id", modelRouteCR.Name)
		return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
	} else {
		defer response.Body.Close()
		contents, err := ioutil.ReadAll(response.Body)
		if err != nil {
			log.Error(err, "Can not get swagger response for model", "mr id", modelRouteCR.Name)
			return reconcile.Result{RequeueAfter: defaultRequeueDelay}, nil
		}

		err = r.mrc.AddModelRoute(modelRouteCR, contents)
		if err != nil {
			return reconcile.Result{}, err
		}
	}

	return reconcile.Result{}, nil

}
