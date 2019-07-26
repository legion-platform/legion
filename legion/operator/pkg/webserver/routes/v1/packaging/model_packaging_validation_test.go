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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	conn_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"testing"

	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	mp_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging/kubernetes"
	pack_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
)

var (
	piIdMpValid           = "pi-id"
	piEntrypointMpValid   = "/usr/bin/test"
	piImageMpValid        = "test:image"
	piArtifactNameMpValid = "some-artifact-name.zip"
	piTrainingIdMpValid   = "training-id"
	connDockerTypeMpValid = "docker-conn"
	connS3TypeMpValid     = "s3-conn"
	piArgumentsMpValid    = packaging.JsonSchema{
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
			{
				Name: "argument-2",
				Parameters: []packaging.Parameter{
					{
						Name:  "type",
						Value: "string",
					},
				},
			},
		},
		Required: []string{"argument-1"},
	}
	piTargetsMpValid = []v1alpha1.TargetSchema{
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

type ModelPackagingValidationSuite struct {
	suite.Suite
	g           *GomegaWithT
	mpStorage   mp_storage.Storage
	connStorage conn_storage.Storage
}

func (s *ModelPackagingValidationSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelPackagingValidationSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.mpStorage = mp_k8s_storage.NewStorage(testNamespace, testNamespace, mgr.GetClient(), nil)
	s.connStorage = conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient())

	err = s.mpStorage.CreatePackagingIntegration(&packaging.PackagingIntegration{
		Id: piIdMpValid,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   piEntrypointMpValid,
			DefaultImage: piImageMpValid,
			Schema: packaging.Schema{
				Targets:   piTargetsMpValid,
				Arguments: piArgumentsMpValid,
			},
		},
	})
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	err = s.connStorage.CreateConnection(&connection.Connection{
		Id: connDockerTypeMpValid,
		Spec: v1alpha1.ConnectionSpec{
			Type: connection.DockerType,
		},
		Status: nil,
	})
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	err = s.connStorage.CreateConnection(&connection.Connection{
		Id: connS3TypeMpValid,
		Spec: v1alpha1.ConnectionSpec{
			Type: connection.S3Type,
		},
		Status: nil,
	})
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}
}

func (s *ModelPackagingValidationSuite) TearDownSuite() {
	if err := s.connStorage.DeleteConnection(connS3TypeMpValid); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	if err := s.connStorage.DeleteConnection(connDockerTypeMpValid); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	if err := s.mpStorage.DeletePackagingIntegration(piIdMpValid); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}
}

func TestModelPackagingValidationSuite(t *testing.T) {
	suite.Run(t, new(ModelPackagingValidationSuite))
}

func (s *ModelPackagingValidationSuite) TestMpIdGeneration() {

	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{},
	}

	_ = pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(ti.Id).ShouldNot(BeEmpty())
}

func (s *ModelPackagingValidationSuite) TestMpIdExplicitly() {
	id := "some-id"
	ti := &packaging.ModelPackaging{
		Id:   id,
		Spec: packaging.ModelPackagingSpec{},
	}

	_ = pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(ti.Id).Should(Equal(id))
}

func (s *ModelPackagingValidationSuite) TestMpImage() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
		},
	}

	_ = pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(ti.Spec.Image).ShouldNot(BeEmpty())
	s.g.Expect(ti.Spec.Image).Should(Equal(piImageMpValid))
}

func (s *ModelPackagingValidationSuite) TestMpImageExplicitly() {
	image := "some-image"
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Image:           image,
		},
	}

	_ = pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(ti.Spec.Image).Should(Equal(image))
}

func (s *ModelPackagingValidationSuite) TestMpImageNotFound() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: "not found",
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("packagingintegrations.legion.legion-platform.org \"not found\" not found"))
}

func (s *ModelPackagingValidationSuite) TestMpArtifactName() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			ArtifactName: piArtifactNameMpValid,
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).ShouldNot(ContainSubstring(pack_route.TrainingIdOrArtifactNameErrorMessage))
}

func (s *ModelPackagingValidationSuite) TestMpArtifactNameMissed() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(pack_route.TrainingIdOrArtifactNameErrorMessage))
}

func (s *ModelPackagingValidationSuite) TestMpIntegrationNameEmpty() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(pack_route.EmptyIntegrationNameErrorMessage))
}

func (s *ModelPackagingValidationSuite) TestMpIntegrationNotFound() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: "some-packaging-name",
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("packagingintegrations.legion.legion-platform.org \"some-packaging-name\" not found"))
}

func (s *ModelPackagingValidationSuite) TestMpNotValidArgumentsSchema() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Arguments: map[string]interface{}{
				"argument-1": 4,
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("argument-1: Must be greater than or equal to 5"))
}

func (s *ModelPackagingValidationSuite) TestMpAdditionalArguments() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Arguments: map[string]interface{}{
				"argument-3": "value",
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("Additional property argument-3 is not allowed"))
}

func (s *ModelPackagingValidationSuite) TestMpRequiredArguments() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Arguments: map[string]interface{}{
				"argument-2": "value",
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("argument-1 is required"))
}

func (s *ModelPackagingValidationSuite) TestMpRequiredTargets() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Targets: []v1alpha1.Target{
				{
					Name:           "target-1",
					ConnectionName: connS3TypeMpValid,
				},
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("[target-2] are required targets"))
}

func (s *ModelPackagingValidationSuite) TestMpNotFoundTargets() {
	targetNotFoundName := "target-not-found"
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Targets: []v1alpha1.Target{
				{
					Name:           targetNotFoundName,
					ConnectionName: connS3TypeMpValid,
				},
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(pack_route.TargetNotFoundErrorMessage, targetNotFoundName, piIdMpValid)))
}

func (s *ModelPackagingValidationSuite) TestMpTargetConnNotFound() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Targets: []v1alpha1.Target{
				{
					Name:           "target-1",
					ConnectionName: "conn-not-found",
				},
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("connections.legion.legion-platform.org \"conn-not-found\" not found"))
}

func (s *ModelPackagingValidationSuite) TestMpTargetConnWrongType() {
	ti := &packaging.ModelPackaging{
		Spec: packaging.ModelPackagingSpec{
			IntegrationName: piIdMpValid,
			Targets: []v1alpha1.Target{
				{
					Name:           "target-1",
					ConnectionName: connDockerTypeMpValid,
				},
			},
		},
	}

	err := pack_route.NewMpValidator(s.mpStorage, s.connStorage).ValidateAndSetDefaults(ti)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(pack_route.NotValidConnTypeErrorMessage, "target-1", connection.DockerType, piIdMpValid)))
}
