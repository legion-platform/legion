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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logC      = logf.Log.WithName("connection--repository")
	MaxSize   = 500
	FirstPage = 0
)

type k8sConnectionRepository struct {
	k8sClient client.Client
	namespace string
}

func NewRepository(namespace string, k8sClient client.Client) conn_repository.Repository {
	return &k8sConnectionRepository{
		namespace: namespace,
		k8sClient: k8sClient,
	}
}

func transformToLabels(conn *connection.Connection) map[string]string {
	return map[string]string{
		"type": string(conn.Spec.Type),
	}
}

func transform(conn *v1alpha1.Connection) *connection.Connection {
	return &connection.Connection{
		ID:     conn.Name,
		Spec:   conn.Spec,
		Status: &conn.Status,
	}
}

func (kc *k8sConnectionRepository) GetConnection(name string) (*connection.Connection, error) {
	k8sConn := &v1alpha1.Connection{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: name, Namespace: kc.namespace},
		k8sConn,
	); err != nil {
		logC.Error(err, "Get connection from k8s", "name", name)

		return nil, err
	}

	return transform(k8sConn), nil
}

func (kc *k8sConnectionRepository) GetConnectionList(options ...conn_repository.ListOption) (
	[]connection.Connection, error,
) {
	var k8sConnList v1alpha1.ConnectionList

	listOptions := &conn_repository.ListOptions{
		Filter: &conn_repository.Filter{},
		Page:   &FirstPage,
		Size:   &MaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	labelSelector, err := kubernetes.TransformFilter(listOptions.Filter, conn_repository.TagKey)
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
		}, &k8sConnList); err != nil {
			logC.Error(err, "Get connection from k8s")

			return nil, err
		}

		continueToken = k8sConnList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	conns := make([]connection.Connection, len(k8sConnList.Items))
	for i := 0; i < len(k8sConnList.Items); i++ {
		currentConn := k8sConnList.Items[i]

		conns[i] = connection.Connection{ID: currentConn.Name, Spec: currentConn.Spec, Status: &currentConn.Status}
	}

	return conns, nil
}

func (kc *k8sConnectionRepository) DeleteConnection(name string) error {
	conn := &v1alpha1.Connection{
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

func (kc *k8sConnectionRepository) UpdateConnection(connection *connection.Connection) error {
	var k8sConn v1alpha1.Connection
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: connection.ID, Namespace: kc.namespace},
		&k8sConn,
	); err != nil {
		logC.Error(err, "Get connection from k8s", "name", connection.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	k8sConn.Spec = connection.Spec
	k8sConn.ObjectMeta.Labels = transformToLabels(connection)

	if err := kc.k8sClient.Update(context.TODO(), &k8sConn); err != nil {
		logC.Error(err, "Creation of the connection", "name", connection.ID)

		return err
	}

	return nil
}

func (kc *k8sConnectionRepository) CreateConnection(connection *connection.Connection) error {
	conn := &v1alpha1.Connection{
		ObjectMeta: metav1.ObjectMeta{
			Name:      connection.ID,
			Namespace: kc.namespace,
			Labels:    transformToLabels(connection),
		},
		Spec: connection.Spec,
	}

	if err := kc.k8sClient.Create(context.TODO(), conn); err != nil {
		logC.Error(err, "ConnectionName creation error from k8s", "name", connection.ID)

		return err
	}

	return nil
}
