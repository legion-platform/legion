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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logC      = logf.Log.WithName("toolchain-integration--repository")
	MaxSize   = 500
	FirstPage = 0
)

func transform(mr *v1alpha1.ToolchainIntegration) *training.ToolchainIntegration {
	return &training.ToolchainIntegration{
		ID:     mr.Name,
		Spec:   mr.Spec,
		Status: &mr.Status,
	}
}

func (kc *trainingK8sRepository) GetToolchainIntegration(name string) (*training.ToolchainIntegration, error) {
	k8sMR := &v1alpha1.ToolchainIntegration{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: name, Namespace: kc.tiNamespace},
		k8sMR,
	); err != nil {
		logC.Error(err, "Get Toolchain Integration from k8s", "name", name)

		return nil, err
	}

	return transform(k8sMR), nil
}

func (kc *trainingK8sRepository) GetToolchainIntegrationList(options ...kubernetes.ListOption) (
	[]training.ToolchainIntegration, error,
) {
	var k8sMRList v1alpha1.ToolchainIntegrationList

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
			Namespace:     kc.tiNamespace,
			Raw: &metav1.ListOptions{
				Limit:    int64(*listOptions.Size),
				Continue: continueToken,
			},
		}, &k8sMRList); err != nil {
			logC.Error(err, "Get Toolchain Integration from k8s")

			return nil, err
		}

		continueToken = k8sMRList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	tis := make([]training.ToolchainIntegration, len(k8sMRList.Items))
	for i := 0; i < len(k8sMRList.Items); i++ {
		currentTI := k8sMRList.Items[i]

		tis[i] = training.ToolchainIntegration{ID: currentTI.Name, Spec: currentTI.Spec, Status: &currentTI.Status}
	}

	return tis, nil
}

func (kc *trainingK8sRepository) DeleteToolchainIntegration(name string) error {
	tis := &v1alpha1.ToolchainIntegration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: kc.tiNamespace,
		},
	}

	if err := kc.k8sClient.Delete(context.TODO(),
		tis,
	); err != nil {
		logC.Error(err, "Delete Packaging Integration from k8s", "name", name)

		return err
	}

	return nil
}

func (kc *trainingK8sRepository) UpdateToolchainIntegration(ti *training.ToolchainIntegration) error {
	var k8sTi v1alpha1.ToolchainIntegration
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: ti.ID, Namespace: kc.tiNamespace},
		&k8sTi,
	); err != nil {
		logC.Error(err, "Update toolchain integration from k8s", "name", ti.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	k8sTi.Spec = ti.Spec

	if err := kc.k8sClient.Update(context.TODO(), &k8sTi); err != nil {
		logC.Error(err, "Creation of the toolchain integration", "name", ti.ID)

		return err
	}

	return nil
}

func (kc *trainingK8sRepository) CreateToolchainIntegration(ti *training.ToolchainIntegration) error {
	k8sTi := &v1alpha1.ToolchainIntegration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      ti.ID,
			Namespace: kc.tiNamespace,
		},
		Spec: ti.Spec,
	}

	if err := kc.k8sClient.Create(context.TODO(), k8sTi); err != nil {
		logC.Error(err, "Toolchain integration creation error from k8s", "name", ti.ID)

		return err
	}

	return nil
}
