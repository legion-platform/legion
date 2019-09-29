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

package kubernetes_test

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"testing"

	. "github.com/onsi/gomega"
)

const (
	mrName = "test-mr"
)

// TODO: add more tests
func TestStorageModelRoute(t *testing.T) {
	g := NewGomegaWithT(t)

	urlPrefixValue := "/test"
	newUrlPrefixValue := "/new/test"
	created := &deployment.ModelRoute{
		Id: mrName,
		Spec: v1alpha1.ModelRouteSpec{
			UrlPrefix: urlPrefixValue,
			ModelDeploymentTargets: []v1alpha1.ModelDeploymentTarget{
				{
					Name: mdId,
				},
			},
		},
	}

	g.Expect(c.CreateModelRoute(created)).NotTo(HaveOccurred())

	fetched, err := c.GetModelRoute(mrName)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(created.Id))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := &deployment.ModelRoute{
		Id: mrName,
		Spec: v1alpha1.ModelRouteSpec{
			UrlPrefix: urlPrefixValue,
			ModelDeploymentTargets: []v1alpha1.ModelDeploymentTarget{
				{
					Name: mdId,
				},
			},
		},
	}
	updated.Spec.UrlPrefix = newUrlPrefixValue
	g.Expect(c.UpdateModelRoute(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetModelRoute(mrName)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(updated.Id))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.UrlPrefix).To(Equal(newUrlPrefixValue))

	g.Expect(c.DeleteModelRoute(mrName)).NotTo(HaveOccurred())
	_, err = c.GetModelRoute(mrName)
	g.Expect(err).To(HaveOccurred())
}
