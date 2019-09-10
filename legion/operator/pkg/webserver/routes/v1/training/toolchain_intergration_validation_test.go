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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	train_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/training"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"testing"
)

type ToolchainIntegrationValidationSuite struct {
	suite.Suite
	g         *GomegaWithT
	validator *train_route.TiValidator
}

func (s *ToolchainIntegrationValidationSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ToolchainIntegrationValidationSuite) SetupSuite() {
	s.validator = train_route.NewTiValidator()
}

func (s *ToolchainIntegrationValidationSuite) TestToolchainIntegrationValidationSuite(t *testing.T) {
	suite.Run(t, new(ToolchainIntegrationValidationSuite))
}

func (s *ToolchainIntegrationValidationSuite) TestTiIdGeneration(t *testing.T) {
	ti := &training.ToolchainIntegration{
		Spec: v1alpha1.ToolchainIntegrationSpec{},
	}

	_ = s.validator.ValidatesAndSetDefaults(ti)
	s.g.Expect(ti.Id).ShouldNot(BeEmpty())
}

func (s *ToolchainIntegrationValidationSuite) TestTiEntrypointEmpty(t *testing.T) {
	ti := &training.ToolchainIntegration{
		Spec: v1alpha1.ToolchainIntegrationSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(ti)
	s.g.Expect(err).ShouldNot(BeNil())
	s.g.Expect(err.Error()).Should(ContainSubstring(train_route.EmptyEntrypointErrorMessage))
}

func (s *ToolchainIntegrationValidationSuite) TestTiDefaultImageEmpty(t *testing.T) {
	ti := &training.ToolchainIntegration{
		Spec: v1alpha1.ToolchainIntegrationSpec{},
	}

	err := s.validator.ValidatesAndSetDefaults(ti)
	s.g.Expect(err).ShouldNot(BeNil())
	s.g.Expect(err.Error()).Should(ContainSubstring(train_route.EmptyDefaultImageErrorMessage))
}
