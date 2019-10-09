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

package training_test

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	conn_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/kubernetes"
	mt_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	mt_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	train_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/training"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"testing"
)

// TODO: add multiple test error

type ModelTrainingValidationSuite struct {
	suite.Suite
	g              *GomegaWithT
	validator      *train_route.MtValidator
	mtRepository   mt_repository.Repository
	connRepository conn_repository.Repository
}

func (s *ModelTrainingValidationSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelTrainingValidationSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.mtRepository = mt_k8s_repository.NewRepository(testNamespace, testNamespace, mgr.GetClient(), nil)
	s.connRepository = conn_k8s_repository.NewRepository(testNamespace, mgr.GetClient())
	s.validator = train_route.NewMtValidator(s.mtRepository, s.connRepository)

	// Create the connection that will be used as the vcs param for a training.
	if err := s.connRepository.CreateConnection(&connection.Connection{
		ID: testMtVCSID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			Reference: testVcsReference,
		},
	}); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	// Create the toolchain integration that will be used for a training.
	if err := s.mtRepository.CreateToolchainIntegration(&training.ToolchainIntegration{
		ID: testToolchainIntegrationID,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			DefaultImage: testToolchainMtImage,
		},
	}); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}
}

func (s *ModelTrainingValidationSuite) TearDownSuite() {
	if err := s.mtRepository.DeleteToolchainIntegration(testToolchainIntegrationID); err != nil {
		panic(err)
	}

	if err := s.connRepository.DeleteConnection(testMtVCSID); err != nil {
		panic(err)
	}
}

func (s *ModelTrainingValidationSuite) TestModelTrainingValidationSuite(t *testing.T) {
	suite.Run(t, new(ModelTrainingValidationSuite))
}

func (s *ModelTrainingValidationSuite) TestMtDefaultResource() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.Spec.Resources).ShouldNot(BeNil())
	s.g.Expect(*mt.Spec.Resources).Should(Equal(train_route.DefaultTrainingResources))
}

func (s *ModelTrainingValidationSuite) TestMtVcsReference() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName: testMtVCSID,
		},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.Spec.Reference).To(Equal(testVcsReference))
}

func (s *ModelTrainingValidationSuite) TestMtMtImage() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Toolchain: testToolchainIntegrationID,
		},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.Spec.Image).To(Equal(testToolchainMtImage))
}

func (s *ModelTrainingValidationSuite) TestMtMtImageExplicitly() {
	image := "image-test"
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Toolchain: testToolchainIntegrationID,
			Image:     image,
		},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.Spec.Image).To(Equal(image))
}

func (s *ModelTrainingValidationSuite) TestMtIDGeneration() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.ID).ShouldNot(BeEmpty())
}

func (s *ModelTrainingValidationSuite) TestMtExplicitMTReference() {
	mtExplicitReference := "test-ref"
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName:   testMtVCSID,
			Reference: mtExplicitReference,
		},
	}

	_ = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(mt.Spec.Reference).To(Equal(mtExplicitReference))
}

func (s *ModelTrainingValidationSuite) TestMtNotExplicitMTReference() {
	conn := &connection.Connection{
		ID: "vcs",
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			Reference: "",
		},
	}

	err := s.connRepository.CreateConnection(conn)
	s.g.Expect(err).Should(BeNil())
	defer s.connRepository.DeleteConnection(conn.ID)

	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName:   conn.ID,
			Reference: "",
		},
	}

	err = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).ShouldNot(BeNil())
	s.g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(train_route.WrongVcsReferenceErrorMessage, conn.ID)))
}

func (s *ModelTrainingValidationSuite) TestMtEmptyVcsName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).ShouldNot(BeNil())
	s.g.Expect(err.Error()).To(ContainSubstring(train_route.EmptyVcsNameMessageError))
}

func (s *ModelTrainingValidationSuite) TestMtWrongVcsConnectionType() {
	conn := &connection.Connection{
		ID: "wrong-type",
		Spec: v1alpha1.ConnectionSpec{
			Type: connection.S3Type,
		},
	}

	err := s.connRepository.CreateConnection(conn)
	s.g.Expect(err).Should(BeNil())
	defer s.connRepository.DeleteConnection(conn.ID)

	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName: conn.ID,
		},
	}

	err = s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).ShouldNot(BeNil())
	s.g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(train_route.WrongVcsTypeErrorMessage, conn.Spec.Type)))
}

func (s *ModelTrainingValidationSuite) TestMtToolchainType() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Toolchain: "not-exists",
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(
		"toolchainintegrations.legion.legion-platform.org \"not-exists\" not found"))
}

func (s *ModelTrainingValidationSuite) TestMtVcsNotExists() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName: "not-exists",
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(
		"connections.legion.legion-platform.org \"not-exists\" not found"))
}

func (s *ModelTrainingValidationSuite) TestMtVcsEmptyName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			VCSName: "",
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(train_route.EmptyVcsNameMessageError))
}

func (s *ModelTrainingValidationSuite) TestMtToolchainEmptyName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Toolchain: "",
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(train_route.ToolchainEmptyErrorMessage))
}

func (s *ModelTrainingValidationSuite) TestMtEmptyModelName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(train_route.EmptyModelNameErrorMessage))
}

func (s *ModelTrainingValidationSuite) TestMtEmptyModelVersion() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(train_route.EmptyModelVersionErrorMessage))
}

func (s *ModelTrainingValidationSuite) TestMtGenerationOutputArtifactName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(mt.Spec.Model.ArtifactNameTemplate).ShouldNot(BeEmpty())
}

func (s *ModelTrainingValidationSuite) TestMtWrongDataType() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Data: []v1alpha1.DataBindingDir{
				{
					Connection: testMtVCSID,
					LocalPath:  testMtDataPath,
				},
			},
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(
		"legion-test data binding has wrong data type. " +
			"Currently supported the following types of connections for data bindings:"))
}

func (s *ModelTrainingValidationSuite) TestMtEmptyDataName() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Data: []v1alpha1.DataBindingDir{
				{
					Connection: "",
					LocalPath:  testMtDataPath,
				},
			},
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(
		train_route.EmptyDataBindingNameErrorMessage, 0)))
}

func (s *ModelTrainingValidationSuite) TestMtEmptyDataPath() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Data: []v1alpha1.DataBindingDir{
				{
					Connection: testMtVCSID,
					LocalPath:  "",
				},
			},
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(fmt.Sprintf(
		train_route.EmptyDataBindingPathErrorMessage, 0)))
}

func (s *ModelTrainingValidationSuite) TestMtNotFoundData() {
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Data: []v1alpha1.DataBindingDir{
				{
					Connection: "not-present",
					LocalPath:  testMtDataPath,
				},
			},
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring(
		"connections.legion.legion-platform.org \"not-present\" not found"))
}

func (s *ModelTrainingValidationSuite) TestMtResourcesValidation() {
	wrongResourceValue := "wrong res"
	mt := &training.ModelTraining{
		Spec: v1alpha1.ModelTrainingSpec{
			Resources: &v1alpha1.ResourceRequirements{
				Limits: &v1alpha1.ResourceList{
					Memory: &wrongResourceValue,
					GPU:    &wrongResourceValue,
					CPU:    &wrongResourceValue,
				},
				Requests: &v1alpha1.ResourceList{
					Memory: &wrongResourceValue,
					GPU:    &wrongResourceValue,
					CPU:    &wrongResourceValue,
				},
			},
		},
	}

	err := s.validator.ValidatesAndSetDefaults(mt)
	s.g.Expect(err).Should(HaveOccurred())

	errorMessage := err.Error()
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of memory request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of cpu request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of gpu request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of memory limit is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of cpu limit is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring(
		"validation of gpu limit is failed: quantities must match the regular expression"))
}
