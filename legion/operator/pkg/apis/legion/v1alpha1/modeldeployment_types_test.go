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

package v1alpha1

import (
	"testing"

	. "github.com/onsi/gomega"
	"golang.org/x/net/context"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
)

const (
	mdImage    = "test:image"
	mdNewImage = "test:new_image"
	mdName     = "foo"
)

func TestStorageModelDeployment(t *testing.T) {
	g := NewGomegaWithT(t)

	mdKey := types.NamespacedName{
		Name:      mdName,
		Namespace: testNamespace,
	}
	created := &ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: ModelDeploymentSpec{
			Image: mdImage,
		},
	}

	g.Expect(created.DeepCopy().ValidatesAndSetDefaults()).NotTo(HaveOccurred())
	g.Expect(c.Create(context.TODO(), created)).NotTo(HaveOccurred())

	fetched := &ModelDeployment{}
	g.Expect(c.Get(context.TODO(), mdKey, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(created))

	updated := fetched.DeepCopy()
	updated.Spec.Image = mdNewImage
	g.Expect(c.Update(context.TODO(), updated)).NotTo(HaveOccurred())

	g.Expect(c.Get(context.TODO(), mdKey, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(updated))
	g.Expect(fetched.Spec.Image).To(Equal(mdNewImage))

	g.Expect(c.Delete(context.TODO(), fetched)).NotTo(HaveOccurred())
	g.Expect(c.Get(context.TODO(), mdKey, fetched)).To(HaveOccurred())
}

func TestMDDefaultValues(t *testing.T) {
	g := NewGomegaWithT(t)

	md := ModelDeployment{
		Spec: ModelDeploymentSpec{},
	}
	_ = md.ValidatesAndSetDefaults()

	g.Expect(*md.Spec.MinReplicas).To(Equal(mdDefaultMinimumReplicas))
	g.Expect(*md.Spec.MaxReplicas).To(Equal(mdDefaultMaximumReplicas))
	g.Expect(*md.Spec.Resources).To(Equal(*mdDefaultResources))
	g.Expect(*md.Spec.ReadinessProbeInitialDelay).To(Equal(mdDefaultReadinessProbeInitialDelay))
	g.Expect(*md.Spec.LivenessProbeInitialDelay).To(Equal(mdDefaultLivenessProbeInitialDelay))
}

func TestValidateMinimumReplicas(t *testing.T) {
	g := NewGomegaWithT(t)

	minReplicas := int32(-1)
	md := ModelDeployment{
		Spec: ModelDeploymentSpec{
			MinReplicas: &minReplicas,
		},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdMinReplicasErrorMessage))
}

func TestValidateMaximumReplicas(t *testing.T) {
	g := NewGomegaWithT(t)

	maxReplicas := int32(-1)
	md := ModelDeployment{
		Spec: ModelDeploymentSpec{
			MaxReplicas: &maxReplicas,
		},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdMaxReplicasErrorMessage))
}

func TestValidateMinLessMaxReplicas(t *testing.T) {
	g := NewGomegaWithT(t)

	minReplicas := int32(2)
	maxReplicas := int32(1)
	md := ModelDeployment{
		Spec: ModelDeploymentSpec{
			MinReplicas: &minReplicas,
			MaxReplicas: &maxReplicas,
		},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdMinMoreThanMinReplicasErrorMessage))
}

func TestValidateImage(t *testing.T) {
	g := NewGomegaWithT(t)

	md := ModelDeployment{
		Spec: ModelDeploymentSpec{},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdEmptyImageErrorMessage))
}

func TestValidateReadinessProbe(t *testing.T) {
	g := NewGomegaWithT(t)

	readinessProbe := int32(-1)
	md := ModelDeployment{
		Spec: ModelDeploymentSpec{
			ReadinessProbeInitialDelay: &readinessProbe,
		},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdReadinessProbeErrorMessage))
}

func TestValidateLivenessProbe(t *testing.T) {
	g := NewGomegaWithT(t)

	livenessProbe := int32(-1)
	md := ModelDeployment{
		Spec: ModelDeploymentSpec{
			LivenessProbeInitialDelay: &livenessProbe,
		},
	}

	err := md.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mdLivenessProbeErrorMessage))
}
