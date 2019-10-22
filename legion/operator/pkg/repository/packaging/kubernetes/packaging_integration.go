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
	"encoding/json"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logPI     = logf.Log.WithName("packaging-integration--repository")
	MaxSize   = 500
	FirstPage = 0
)

// We should save the arguments structure inside json string in k8s -repository
// Because before < 2.0.0 kubebuilder, it can not handle interface{} field.
// TODO: make upgrade https://github.com/kubernetes-sigs/kubebuilder/releases/tag/v2.0.0
func TransformPackagingIntegrationFromK8s(pi *v1alpha1.PackagingIntegration) (*packaging.PackagingIntegration, error) {
	var argumentsValidation []packaging.Property
	if err := json.Unmarshal([]byte(pi.Spec.Schema.Arguments.Properties), &argumentsValidation); err != nil {
		return nil, err
	}

	return &packaging.PackagingIntegration{
		ID: pi.Name,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   pi.Spec.Entrypoint,
			DefaultImage: pi.Spec.DefaultImage,
			Privileged:   pi.Spec.Privileged,
			Schema: packaging.Schema{
				Targets: pi.Spec.Schema.Targets,
				Arguments: packaging.JsonSchema{
					Properties: argumentsValidation,
					Required:   pi.Spec.Schema.Arguments.Required,
				},
			},
		},
		Status: &pi.Status,
	}, nil
}

// Take a look to the documentation of TransformPackagingIntegrationFromK8s
func TransformPiToK8s(pi *packaging.PackagingIntegration, k8sNamespace string) (*v1alpha1.PackagingIntegration, error) {
	var piStatus v1alpha1.PackagingIntegrationStatus
	if pi.Status != nil {
		piStatus = *pi.Status
	}

	argumentsValidationBytes, err := json.Marshal(pi.Spec.Schema.Arguments.Properties)
	if err != nil {
		return nil, err
	}

	return &v1alpha1.PackagingIntegration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      pi.ID,
			Namespace: k8sNamespace,
		},
		Spec: v1alpha1.PackagingIntegrationSpec{
			Entrypoint:   pi.Spec.Entrypoint,
			DefaultImage: pi.Spec.DefaultImage,
			Privileged:   pi.Spec.Privileged,
			Schema: v1alpha1.SchemaValidation{
				Targets: pi.Spec.Schema.Targets,
				Arguments: v1alpha1.JsonSchema{
					Properties: string(argumentsValidationBytes),
					Required:   pi.Spec.Schema.Arguments.Required,
				},
			},
		},
		Status: piStatus,
	}, nil
}

func (pkr *packagingK8sRepository) GetPackagingIntegration(name string) (*packaging.PackagingIntegration, error) {
	k8sMR := &v1alpha1.PackagingIntegration{}
	if err := pkr.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: name, Namespace: pkr.piNamespace},
		k8sMR,
	); err != nil {
		logPI.Error(err, "Get Packaging Integration from k8s", "name", name)

		return nil, err
	}

	return TransformPackagingIntegrationFromK8s(k8sMR)
}

func (pkr *packagingK8sRepository) GetPackagingIntegrationList(options ...kubernetes.ListOption) (
	[]packaging.PackagingIntegration, error,
) {
	var k8sMRList v1alpha1.PackagingIntegrationList

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
		logPI.Error(err, "Generate label selector")
		return nil, err
	}
	continueToken := ""

	for i := 0; i < *listOptions.Page+1; i++ {
		if err := pkr.k8sClient.List(context.TODO(), &client.ListOptions{
			LabelSelector: labelSelector,
			Namespace:     pkr.piNamespace,
			Raw: &metav1.ListOptions{
				Limit:    int64(*listOptions.Size),
				Continue: continueToken,
			},
		}, &k8sMRList); err != nil {
			logPI.Error(err, "Get Packaging Integration from k8s")

			return nil, err
		}

		continueToken = k8sMRList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	pis := make([]packaging.PackagingIntegration, len(k8sMRList.Items))
	for i := 0; i < len(k8sMRList.Items); i++ {
		k8sPi := k8sMRList.Items[i]

		if pi, err := TransformPackagingIntegrationFromK8s(&k8sPi); err != nil {
			logPI.Error(err, "Get Packaging Integration from k8s")

		} else {
			pis[i] = *pi
		}
	}

	return pis, nil
}

func (pkr *packagingK8sRepository) DeletePackagingIntegration(name string) error {
	pi := &v1alpha1.PackagingIntegration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: pkr.piNamespace,
		},
	}

	if err := pkr.k8sClient.Delete(context.TODO(), pi); err != nil {
		logPI.Error(err, "Delete Packaging Integration from k8s", "name", name)

		return err
	}

	return nil
}

func (pkr *packagingK8sRepository) UpdatePackagingIntegration(pi *packaging.PackagingIntegration) error {
	var k8sPi v1alpha1.PackagingIntegration
	if err := pkr.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: pi.ID, Namespace: pkr.piNamespace},
		&k8sPi,
	); err != nil {
		logPI.Error(err, "Get packaging integration from k8s", "name", pi.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	updateK8sPi, err := TransformPiToK8s(pi, pkr.piNamespace)
	if err != nil {
		return err
	}

	k8sPi.Spec = updateK8sPi.Spec

	if err := pkr.k8sClient.Update(context.TODO(), &k8sPi); err != nil {
		logPI.Error(err, "Creation of the packaging integration", "name", pi.ID)

		return err
	}

	return nil
}

func (pkr *packagingK8sRepository) CreatePackagingIntegration(pi *packaging.PackagingIntegration) error {
	k8sPi, err := TransformPiToK8s(pi, pkr.piNamespace)
	if err != nil {
		return err
	}

	if err := pkr.k8sClient.Create(context.TODO(), k8sPi); err != nil {
		logPI.Error(err, "Packaging integration creation error from k8s", "name", pi.ID)

		return err
	}

	return nil
}
