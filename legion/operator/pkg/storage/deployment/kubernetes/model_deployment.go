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
	md_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logMD       = logf.Log.WithName("model-deployment-storage")
	MDMaxSize   = 500
	MDFirstPage = 0
)

func mdTransformToLabels(md *deployment.ModelDeployment) map[string]string {
	return map[string]string{
		"roleName": *md.Spec.RoleName,
	}
}

func mdTransform(k8sMD *v1alpha1.ModelDeployment) *deployment.ModelDeployment {
	return &deployment.ModelDeployment{
		Id:     k8sMD.Name,
		Spec:   k8sMD.Spec,
		Status: &k8sMD.Status,
	}
}

func (kc *deploymentK8sStorage) GetModelDeployment(name string) (*deployment.ModelDeployment, error) {
	k8sMD := &v1alpha1.ModelDeployment{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: name, Namespace: kc.namespace},
		k8sMD,
	); err != nil {
		logMD.Error(err, "Get Model Deployment from k8s", "name", name)

		return nil, err
	}

	return mdTransform(k8sMD), nil
}

func (kc *deploymentK8sStorage) GetModelDeploymentList(options ...kubernetes.ListOption) ([]deployment.ModelDeployment, error) {
	var k8sMDList v1alpha1.ModelDeploymentList

	listOptions := &kubernetes.ListOptions{
		Filter: nil,
		Page:   &MDFirstPage,
		Size:   &MDMaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	labelSelector, err := kubernetes.TransformFilter(listOptions.Filter, md_storage.TagKey)
	if err != nil {
		logMD.Error(err, "Generate label selector")
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
		}, &k8sMDList); err != nil {
			logMD.Error(err, "Get Model Deployment from k8s")

			return nil, err
		}

		continueToken = k8sMDList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	mds := make([]deployment.ModelDeployment, len(k8sMDList.Items))
	for i := 0; i < len(k8sMDList.Items); i++ {
		currentMD := k8sMDList.Items[i]

		mds[i] = deployment.ModelDeployment{Id: currentMD.Name, Spec: currentMD.Spec, Status: &currentMD.Status}
	}

	return mds, nil
}

func (kc *deploymentK8sStorage) DeleteModelDeployment(name string) error {
	md := &v1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: kc.namespace,
		},
	}

	if err := kc.k8sClient.Delete(context.TODO(),
		md,
		client.PropagationPolicy(kc.mdDeleteOption),
	); err != nil {
		logMD.Error(err, "Delete Model Deployment from k8s", "name", name)

		return err
	}

	return nil
}

func (kc *deploymentK8sStorage) UpdateModelDeployment(md *deployment.ModelDeployment) error {
	var k8sMD v1alpha1.ModelDeployment
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: md.Id, Namespace: kc.namespace},
		&k8sMD,
	); err != nil {
		logMD.Error(err, "Get Model Deployment from k8s", "name", md.Id)

		return err
	}

	// TODO: think about update, not replacing as for now
	k8sMD.Spec = md.Spec
	k8sMD.ObjectMeta.Labels = mdTransformToLabels(md)

	if err := kc.k8sClient.Update(context.TODO(), &k8sMD); err != nil {
		logMD.Error(err, "Creation of the Model Deployment", "name", md.Id)

		return err
	}

	return nil
}

func (kc *deploymentK8sStorage) CreateModelDeployment(md *deployment.ModelDeployment) error {
	k8sMd := &v1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      md.Id,
			Namespace: kc.namespace,
			Labels:    mdTransformToLabels(md),
		},
		Spec: md.Spec,
	}

	if err := kc.k8sClient.Create(context.TODO(), k8sMd); err != nil {
		logMD.Error(err, "ModelDeployment creation error from k8s", "name", md.Id)

		return err
	}

	return nil
}
