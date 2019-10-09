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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"k8s.io/apimachinery/pkg/api/errors"
	"testing"

	. "github.com/onsi/gomega"
)

const (
	piEntrypoint    = "/usr/bin/test"
	piNewEntrypoint = "/usr/bin/newtest"
	piImage         = "test:image"
	piID            = "pi1"
)

var (
	piArguments = packaging.JsonSchema{
		Properties: []packaging.Property{
			{
				Name: "argument-1",
				Parameters: []packaging.Parameter{
					{
						Name:  "minimum",
						Value: float64(5),
					},
					{
						Name:  "type",
						Value: "number",
					},
				},
			},
		},
		Required: []string{"argument-1"},
	}
	piTargets = []v1alpha1.TargetSchema{
		{
			Name: "target-1",
			ConnectionTypes: []string{
				string(connection.S3Type),
				string(connection.GcsType),
			},
			Required: false,
		},
		{
			Name: "target-2",
			ConnectionTypes: []string{
				string(connection.DockerType),
			},
			Required: true,
		},
	}
)

func TestPackagingIntegrationRepository(t *testing.T) {
	g := NewGomegaWithT(t)

	created := &packaging.PackagingIntegration{
		ID: piID,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   piEntrypoint,
			DefaultImage: piImage,
			Privileged:   false,
			Schema: packaging.Schema{
				Targets:   piTargets,
				Arguments: piArguments,
			},
		},
	}

	g.Expect(c.CreatePackagingIntegration(created)).NotTo(HaveOccurred())

	fetched, err := c.GetPackagingIntegration(piID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(created.ID))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := fetched
	updated.Spec.Entrypoint = piNewEntrypoint
	g.Expect(c.UpdatePackagingIntegration(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetPackagingIntegration(piID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.ID).To(Equal(updated.ID))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.Entrypoint).To(Equal(piNewEntrypoint))

	g.Expect(c.DeletePackagingIntegration(piID)).NotTo(HaveOccurred())
	_, err = c.GetPackagingIntegration(piID)
	g.Expect(err).To(HaveOccurred())
	g.Expect(errors.IsNotFound(err)).Should(BeTrue())
}
