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

package kubernetes

import (
	"context"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logC      = logf.Log.WithName("modelroute--repository")
	MaxSize   = 500
	FirstPage = 0
)

func transform(mr *v1alpha1.ModelRoute) *deployment.ModelRoute {
	return &deployment.ModelRoute{
		ID:     mr.Name,
		Spec:   mr.Spec,
		Status: &mr.Status,
	}
}

func (kc *deploymentK8sRepository) GetModelRoute(name string) (*deployment.ModelRoute, error) {
	k8sMR := &v1alpha1.ModelRoute{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: name, Namespace: kc.namespace},
		k8sMR,
	); err != nil {
		logC.Error(err, "Get Model Route from k8s", "name", name)

		return nil, err
	}

	return transform(k8sMR), nil
}

func (kc *deploymentK8sRepository) GetModelRouteList(options ...kubernetes.ListOption) (
	[]deployment.ModelRoute, error,
) {
	var k8sMRList v1alpha1.ModelRouteList

	listOptions := &kubernetes.ListOptions{
		Filter: nil,
		Page:   &FirstPage,
		Size:   &MaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	labelSelector, err := kubernetes.TransformFilter(listOptions.Filter, "")
	if err != nil {
		logC.Error(err, "Generate label selector")
		return nil, err
	}
	continueToken := ""

	for i := 0; i < *listOptions.Page+1; i++ {
		if err := kc.k8sClient.List(context.TODO(), &client.ListOptions{
			LabelSelector: labelSelector,
			Namespace:     kc.namespace,
			Raw: &metav1.ListOptions{
				Limit:    int64(*listOptions.Size),
				Continue: continueToken,
			},
		}, &k8sMRList); err != nil {
			logC.Error(err, "Get Model Route from k8s")

			return nil, err
		}

		continueToken = k8sMRList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	conns := make([]deployment.ModelRoute, len(k8sMRList.Items))
	for i := 0; i < len(k8sMRList.Items); i++ {
		currentMR := k8sMRList.Items[i]

		conns[i] = deployment.ModelRoute{ID: currentMR.Name, Spec: currentMR.Spec, Status: &currentMR.Status}
	}

	return conns, nil
}

func (kc *deploymentK8sRepository) DeleteModelRoute(name string) error {
	conn := &v1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: kc.namespace,
		},
	}

	if err := kc.k8sClient.Delete(context.TODO(),
		conn,
	); err != nil {
		logC.Error(err, "Delete connection from k8s", "name", name)

		return err
	}

	return nil
}

func (kc *deploymentK8sRepository) UpdateModelRoute(connection *deployment.ModelRoute) error {
	var k8sMR v1alpha1.ModelRoute
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: connection.ID, Namespace: kc.namespace},
		&k8sMR,
	); err != nil {
		logC.Error(err, "Get connection from k8s", "name", connection.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	k8sMR.Spec = connection.Spec

	if err := kc.k8sClient.Update(context.TODO(), &k8sMR); err != nil {
		logC.Error(err, "Creation of the connection", "name", connection.ID)

		return err
	}

	return nil
}

func (kc *deploymentK8sRepository) CreateModelRoute(connection *deployment.ModelRoute) error {
	conn := &v1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      connection.ID,
			Namespace: kc.namespace,
		},
		Spec: connection.Spec,
	}

	if err := kc.k8sClient.Create(context.TODO(), conn); err != nil {
		logC.Error(err, "DataBinding creation error from k8s", "name", connection.ID)

		return err
	}

	return nil
}
