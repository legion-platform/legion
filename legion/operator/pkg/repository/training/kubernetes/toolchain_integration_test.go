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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"testing"

	. "github.com/onsi/gomega"
)

const (
	tiID            = "foo"
	tiEntrypoint    = "test-entrypoint"
	tiNewEntrypoint = "new-test-entrypoint"
)

// TODO: Add more tests
func TestToolchainRepository(t *testing.T) {
	g := NewGomegaWithT(t)

	created := &training.ToolchainIntegration{
		ID: tiID,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			Entrypoint: tiEntrypoint,
		},
	}

	g.Expect(c.CreateToolchainIntegration(created)).NotTo(HaveOccurred())

	fetched, err := c.GetToolchainIntegration(tiID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(created.ID))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := &training.ToolchainIntegration{
		ID: tiID,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			Entrypoint: tiNewEntrypoint,
		},
	}
	g.Expect(c.UpdateToolchainIntegration(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetToolchainIntegration(tiID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(updated.ID))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.Entrypoint).To(Equal(tiNewEntrypoint))

	g.Expect(c.DeleteToolchainIntegration(tiID)).NotTo(HaveOccurred())
	_, err = c.GetToolchainIntegration(tiID)
	g.Expect(err).To(HaveOccurred())
}
