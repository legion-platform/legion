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
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	"github.com/stretchr/testify/suite"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/client-go/kubernetes/scheme"
	"sigs.k8s.io/controller-runtime/pkg/client"
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
				string(connection.AzureBlobType),
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

type PIRepositorySuite struct {
	suite.Suite
	g         *GomegaWithT
	k8sClient client.Client
	rep       mp_repository.Repository
}

func (s *PIRepositorySuite) SetupSuite() {
	var err error
	s.k8sClient, err = client.New(cfg, client.Options{Scheme: scheme.Scheme})
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	k8sClient, err := client.New(cfg, client.Options{Scheme: scheme.Scheme})
	if err != nil {
		// If we get the panic that we have a test configuration problem
		panic(err)
	}

	// k8sConfig is nil because we use this client only for getting logs
	// we do not test this functionality in unit tests
	s.rep = mp_k8s_repository.NewRepository(testNamespace, testNamespace, k8sClient, nil)
}

func (s *PIRepositorySuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *PIRepositorySuite) TearDownTest() {
	if err := s.rep.DeleteModelPackaging(mpID); err != nil && !errors.IsNotFound(err) {
		// If we get the panic that we have a test configuration problem
		panic(err)
	}
}

func TestSuitePI(t *testing.T) {
	suite.Run(t, new(PIRepositorySuite))
}

func (s *PIRepositorySuite) TestPackagingIntegrationRepository() {
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

	s.g.Expect(s.rep.CreatePackagingIntegration(created)).NotTo(HaveOccurred())

	fetched, err := s.rep.GetPackagingIntegration(piID)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(fetched.ID).To(Equal(created.ID))
	s.g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := fetched
	updated.Spec.Entrypoint = piNewEntrypoint
	s.g.Expect(s.rep.UpdatePackagingIntegration(updated)).NotTo(HaveOccurred())

	fetched, err = s.rep.GetPackagingIntegration(piID)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(fetched.ID).To(Equal(updated.ID))
	s.g.Expect(fetched.Spec).To(Equal(updated.Spec))
	s.g.Expect(fetched.Spec.Entrypoint).To(Equal(piNewEntrypoint))

	s.g.Expect(s.rep.DeletePackagingIntegration(piID)).NotTo(HaveOccurred())
	_, err = s.rep.GetPackagingIntegration(piID)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(errors.IsNotFound(err)).Should(BeTrue())
}
