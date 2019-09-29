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

package modeldeployment

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/util/workqueue"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var _ handler.EventHandler = &EnqueueRequestForImplicitOwner{}

var logEH = logf.Log.WithName("modeldeployment-eventhandler")

type EnqueueRequestForImplicitOwner struct{}

func (e *EnqueueRequestForImplicitOwner) Create(evt event.CreateEvent, q workqueue.RateLimitingInterface) {
	// skip
}

func (e *EnqueueRequestForImplicitOwner) Update(evt event.UpdateEvent, q workqueue.RateLimitingInterface) {
	e.addEvent(evt.ObjectOld, evt.MetaOld, q)

	e.addEvent(evt.ObjectNew, evt.MetaNew, q)
}

func (e *EnqueueRequestForImplicitOwner) Delete(evt event.DeleteEvent, q workqueue.RateLimitingInterface) {
	// skip
}

// Generic implements EventHandler
func (e *EnqueueRequestForImplicitOwner) Generic(evt event.GenericEvent, q workqueue.RateLimitingInterface) {
	e.addEvent(evt.Object, evt.Meta, q)
}

func (e *EnqueueRequestForImplicitOwner) addEvent(obj runtime.Object, meta metav1.Object, q workqueue.RateLimitingInterface) {
	labels := meta.GetLabels()
	name, ok := labels[modelNameAnnotationKey]
	if !ok {
		return
	}

	logEH.Info("Trigger model deployment reconcile", "causer", meta.GetSelfLink(), "model deployment id", name)

	q.Add(reconcile.Request{
		NamespacedName: types.NamespacedName{
			Namespace: meta.GetNamespace(),
			Name:      name,
		},
	})
}
