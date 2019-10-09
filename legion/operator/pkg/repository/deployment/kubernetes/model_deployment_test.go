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
	mdImage    = "test:image"
	mdNewImage = "test:new_image"
	mdID       = "test-id"
)

var (
	mdRoleName = "test-tole"
)

// TODO: Add more tests
func TestModelDeploymentRepository(t *testing.T) {
	g := NewGomegaWithT(t)

	created := &deployment.ModelDeployment{
		ID: mdID,
		Spec: v1alpha1.ModelDeploymentSpec{
			Image:    mdImage,
			RoleName: &mdRoleName,
		},
	}

	g.Expect(c.CreateModelDeployment(created)).NotTo(HaveOccurred())

	fetched, err := c.GetModelDeployment(mdID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(created.ID))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := &deployment.ModelDeployment{
		ID: mdID,
		Spec: v1alpha1.ModelDeploymentSpec{
			Image:    mdNewImage,
			RoleName: &mdRoleName,
		},
	}
	g.Expect(c.UpdateModelDeployment(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetModelDeployment(mdID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(updated.ID))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.Image).To(Equal(mdNewImage))

	g.Expect(c.DeleteModelDeployment(mdID)).NotTo(HaveOccurred())
	_, err = c.GetModelDeployment(mdID)
	g.Expect(err).To(HaveOccurred())
}
