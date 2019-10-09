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

package packaging_test

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	pack_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	. "github.com/onsi/gomega"
	"testing"
)

func TestPiIDValidation(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		Spec: packaging.PackagingIntegrationSpec{},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(pack_route.EmptyIDErrorMessage))
}

func TestPiEntrypointValidation(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		Spec: packaging.PackagingIntegrationSpec{},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(pack_route.EmptyEntrypointErrorMessage))
}

func TestPiDefaultImageValidation(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		Spec: packaging.PackagingIntegrationSpec{},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(pack_route.EmptyDefaultImageErrorMessage))
}

func TestPiEmptyTargetsValidation(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).ShouldNot(HaveOccurred())
}

func TestPiEmptyArgumentsValidation(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).ShouldNot(HaveOccurred())
}

func TestPiEmptyTargetName(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
			Schema: packaging.Schema{
				Targets: []v1alpha1.TargetSchema{
					{
						Name:            "",
						ConnectionTypes: nil,
						Required:        false,
					},
				},
			},
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(pack_route.TargetEmptyNameErrorMessage))
}

func TestPiEmptyConnectionType(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	targetName := "some-name"
	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
			Schema: packaging.Schema{
				Targets: []v1alpha1.TargetSchema{
					{
						Name:            targetName,
						ConnectionTypes: nil,
						Required:        false,
					},
				},
			},
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(
		pack_route.TargetEmptyConnectionTypesErrorMessage, targetName,
	)))
}

func TestPiUnknownConnectionType(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()
	unknownConnType := "some-type"
	targetName := "some-name"
	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
			Schema: packaging.Schema{
				Targets: []v1alpha1.TargetSchema{
					{
						Name:            targetName,
						ConnectionTypes: []string{unknownConnType},
						Required:        false,
					},
				},
			},
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(
		pack_route.TargetUnknownConnTypeErrorMessage, targetName, unknownConnType,
	)))
}

func TestPiNotValidJsonSchema(t *testing.T) {
	g := NewGomegaWithT(t)
	createEnvironment()

	pi := &packaging.PackagingIntegration{
		ID: "some-id",
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "some-entrypoint",
			DefaultImage: "some/image:tag",
			Privileged:   false,
			Schema: packaging.Schema{
				Arguments: packaging.JsonSchema{
					Properties: []packaging.Property{
						{
							Name: "some-var",
							Parameters: []packaging.Parameter{
								{
									Name:  "type",
									Value: "bool",
								},
							},
						},
					},
				},
			},
		},
	}

	err := pack_route.NewPiValidator().ValidateAndSetDefaults(pi)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring("given: /bool/ Expected valid values are"))
}
