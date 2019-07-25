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
	"fmt"
	"testing"

	. "github.com/onsi/gomega"
	"golang.org/x/net/context"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
)

const (
	mrName = "test-mr"
	mrUrl  = "/test/url"
)

func TestStorageModelRoute(t *testing.T) {
	g := NewGomegaWithT(t)

	urlPrefixValue := "/test"
	newUrlPrefixValue := "/new/test"
	key := types.NamespacedName{
		Name:      mrName,
		Namespace: testNamespace,
	}
	created := &ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: ModelRouteSpec{
			UrlPrefix: urlPrefixValue,
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name: md1Test.ObjectMeta.Name,
				},
			},
		},
	}

	g.Expect(created.DeepCopy().ValidatesAndSetDefaults(c)).NotTo(HaveOccurred())
	g.Expect(c.Create(context.TODO(), created)).NotTo(HaveOccurred())

	fetched := &ModelRoute{}
	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(created))

	updated := fetched.DeepCopy()
	updated.Spec.UrlPrefix = newUrlPrefixValue
	g.Expect(c.Update(context.TODO(), updated)).NotTo(HaveOccurred())

	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(updated))
	g.Expect(fetched.Spec.UrlPrefix).To(Equal(newUrlPrefixValue))

	g.Expect(c.Delete(context.TODO(), fetched)).NotTo(HaveOccurred())
	g.Expect(c.Get(context.TODO(), key, fetched)).To(HaveOccurred())
}

func TestDefaultValues(t *testing.T) {
	g := NewGomegaWithT(t)

	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name: md1Test.ObjectMeta.Name,
				},
			},
		},
	}

	_ = mr.ValidatesAndSetDefaults(c)

	g.Expect(*mr.Spec.ModelDeploymentTargets[0].Weight).To(Equal(maxWeight))
}

func TestEmptyUrlPrefix(t *testing.T) {
	g := NewGomegaWithT(t)

	mr := &ModelRoute{
		Spec: ModelRouteSpec{},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrUrlPrefixEmptyErrorMessage))
}

func TestNotExistsMirrorMD(t *testing.T) {
	g := NewGomegaWithT(t)

	mirrorMD := "not-exists"
	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			Mirror: &mirrorMD,
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring("modeldeployments.legion.legion-platform.org \"not-exists\" not found"))
}

func TestMissingMDTargets(t *testing.T) {
	g := NewGomegaWithT(t)

	mr := &ModelRoute{
		Spec: ModelRouteSpec{},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrEmptyTargetErrorMessage))
}

func TestOneTargetWrongWeight(t *testing.T) {
	g := NewGomegaWithT(t)

	weight := int32(77)
	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name:   md1Test.ObjectMeta.Name,
					Weight: &weight,
				},
			},
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrOneTargetErrorMessage))
}

func TestOneTargetNotExist(t *testing.T) {
	g := NewGomegaWithT(t)

	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name: "not-exists",
				},
			},
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring("modeldeployments.legion.legion-platform.org \"not-exists\" not found"))
}

func TestMultipleTargetsWrongWeight(t *testing.T) {
	g := NewGomegaWithT(t)

	weight1 := int32(11)
	weight2 := int32(22)
	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name:   md1Test.ObjectMeta.Name,
					Weight: &weight1,
				},
				{
					Name:   md2Test.ObjectMeta.Name,
					Weight: &weight2,
				},
			},
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrTotalWeightErrorMessage))
}

func TestMultipleTargetsMissingWeight(t *testing.T) {
	g := NewGomegaWithT(t)

	weight2 := int32(22)
	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name: md1Test.ObjectMeta.Name,
				},
				{
					Name:   md2Test.ObjectMeta.Name,
					Weight: &weight2,
				},
			},
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrMissedWeightErrorMessage))
}

func TestMultipleTargetsNotExist(t *testing.T) {
	g := NewGomegaWithT(t)

	weight1 := int32(11)
	weight2 := int32(50)
	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			ModelDeploymentTargets: []ModelDeploymentTarget{
				{
					Name:   "not-exists",
					Weight: &weight1,
				},
				{
					Name:   md2Test.ObjectMeta.Name,
					Weight: &weight2,
				},
			},
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring("modeldeployments.legion.legion-platform.org \"not-exists\" not found"))
}

func TestUrlStartWithSlash(t *testing.T) {
	g := NewGomegaWithT(t)

	mr := &ModelRoute{
		Spec: ModelRouteSpec{
			UrlPrefix: "test/test",
		},
	}

	err := mr.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(mrUrlPrefixSlashErrorMessage))
}

func TestForbiddenPrefixes(t *testing.T) {
	g := NewGomegaWithT(t)

	for _, prefix := range forbiddenPrefixes {
		mr := &ModelRoute{
			Spec: ModelRouteSpec{
				UrlPrefix: fmt.Sprintf("%s/test/test", prefix),
			},
		}

		err := mr.ValidatesAndSetDefaults(c)
		g.Expect(err).To(HaveOccurred())
		g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(mrForbiddenPrefix, prefix)))
	}
}

func TestAllowForbiddenPrefixes(t *testing.T) {
	g := NewGomegaWithT(t)

	for _, prefix := range forbiddenPrefixes {
		mr := &ModelRoute{
			ObjectMeta: metav1.ObjectMeta{
				Annotations: map[string]string{
					SkipUrlValidationKey: SkipUrlValidationValue,
				},
			},
			Spec: ModelRouteSpec{
				UrlPrefix: fmt.Sprintf("%s/test/test", prefix),
			},
		}

		err := mr.ValidatesAndSetDefaults(c)
		g.Expect(err).To(HaveOccurred())
		g.Expect(err.Error()).ToNot(ContainSubstring(fmt.Sprintf(mrForbiddenPrefix, prefix)))
	}
}
