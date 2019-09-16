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

package deployment_test

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	md_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/deployment"
	"github.com/stretchr/testify/suite"
	"testing"

	. "github.com/onsi/gomega"
)

var (
	mdRoleName = "test-tole"
)

type ModelDeploymentValidationSuite struct {
	suite.Suite
	g *GomegaWithT
}

func (s *ModelDeploymentValidationSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestModelDeploymentValidationSuite(t *testing.T) {
	suite.Run(t, new(ModelDeploymentValidationSuite))
}

func (s *ModelDeploymentValidationSuite) TestMDMinReplicasDefaultValue() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}
	_ = md_routes.ValidatesMDAndSetDefaults(md)

	s.g.Expect(*md.Spec.MinReplicas).To(Equal(md_routes.MdDefaultMinimumReplicas))
}

func (s *ModelDeploymentValidationSuite) TestMDMaxReplicasDefaultValue() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}
	_ = md_routes.ValidatesMDAndSetDefaults(md)

	s.g.Expect(*md.Spec.MaxReplicas).To(Equal(md_routes.MdDefaultMaximumReplicas))
}

func (s *ModelDeploymentValidationSuite) TestMDResourcesDefaultValues() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}
	_ = md_routes.ValidatesMDAndSetDefaults(md)

	s.g.Expect(*md.Spec.Resources).To(Equal(*md_routes.MdDefaultResources))
}

func (s *ModelDeploymentValidationSuite) TestMDReadinessProbeDefaultValue() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}
	_ = md_routes.ValidatesMDAndSetDefaults(md)

	s.g.Expect(*md.Spec.ReadinessProbeInitialDelay).To(Equal(md_routes.MdDefaultReadinessProbeInitialDelay))
}

func (s *ModelDeploymentValidationSuite) TestMDLivenessProbeDefaultValue() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}
	_ = md_routes.ValidatesMDAndSetDefaults(md)

	s.g.Expect(*md.Spec.LivenessProbeInitialDelay).To(Equal(md_routes.MdDefaultLivenessProbeInitialDelay))
}

func (s *ModelDeploymentValidationSuite) TestValidateMinimumReplicas() {
	minReplicas := int32(-1)
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			MinReplicas: &minReplicas,
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.MinReplicasErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestValidateMaximumReplicas() {
	maxReplicas := int32(-1)
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			MaxReplicas: &maxReplicas,
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.MaxReplicasErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestValidateMinLessMaxReplicas() {
	minReplicas := int32(2)
	maxReplicas := int32(1)
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			MinReplicas: &minReplicas,
			MaxReplicas: &maxReplicas,
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.MinMoreThanMinReplicasErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestValidateImage() {
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.EmptyImageErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestValidateReadinessProbe() {
	readinessProbe := int32(-1)
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			ReadinessProbeInitialDelay: &readinessProbe,
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.ReadinessProbeErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestValidateLivenessProbe() {
	livenessProbe := int32(-1)
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			LivenessProbeInitialDelay: &livenessProbe,
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(err.Error()).To(ContainSubstring(md_routes.LivenessProbeErrorMessage))
}

func (s *ModelDeploymentValidationSuite) TestMdResourcesValidation() {
	wrongResourceValue := "wrong res"
	md := &deployment.ModelDeployment{
		Spec: v1alpha1.ModelDeploymentSpec{
			Resources: &v1alpha1.ResourceRequirements{
				Limits: &v1alpha1.ResourceList{
					Memory: &wrongResourceValue,
					Gpu:    &wrongResourceValue,
					Cpu:    &wrongResourceValue,
				},
				Requests: &v1alpha1.ResourceList{
					Memory: &wrongResourceValue,
					Gpu:    &wrongResourceValue,
					Cpu:    &wrongResourceValue,
				},
			},
		},
	}

	err := md_routes.ValidatesMDAndSetDefaults(md)
	s.g.Expect(err).Should(HaveOccurred())

	errorMessage := err.Error()
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of memory request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of cpu request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of gpu request is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of memory limit is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of cpu limit is failed: quantities must match the regular expression"))
	s.g.Expect(errorMessage).Should(ContainSubstring("validation of gpu limit is failed: quantities must match the regular expression"))
}
