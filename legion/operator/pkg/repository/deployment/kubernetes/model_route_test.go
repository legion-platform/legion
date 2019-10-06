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
func TestModelRouteRepository(t *testing.T) {
	g := NewGomegaWithT(t)

	urlPrefixValue := "/test"
	newURLPrefixValue := "/new/test"
	created := &deployment.ModelRoute{
		ID: mrName,
		Spec: v1alpha1.ModelRouteSpec{
			URLPrefix: urlPrefixValue,
			ModelDeploymentTargets: []v1alpha1.ModelDeploymentTarget{
				{
					Name: mdID,
				},
			},
		},
	}

	g.Expect(c.CreateModelRoute(created)).NotTo(HaveOccurred())

	fetched, err := c.GetModelRoute(mrName)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(created.ID))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := &deployment.ModelRoute{
		ID: mrName,
		Spec: v1alpha1.ModelRouteSpec{
			URLPrefix: urlPrefixValue,
			ModelDeploymentTargets: []v1alpha1.ModelDeploymentTarget{
				{
					Name: mdID,
				},
			},
		},
	}
	updated.Spec.URLPrefix = newURLPrefixValue
	g.Expect(c.UpdateModelRoute(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetModelRoute(mrName)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(updated.ID))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.URLPrefix).To(Equal(newURLPrefixValue))

	g.Expect(c.DeleteModelRoute(mrName)).NotTo(HaveOccurred())
	_, err = c.GetModelRoute(mrName)
	g.Expect(err).To(HaveOccurred())
}
