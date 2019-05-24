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
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	"golang.org/x/net/context"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"testing"
)

const (
	mtName          = "test-md"
	mtToolchainType = "python"
	mtImage         = "test:image"
	mtNewImage      = "test:new-image"
)

func TestStorageModelTraining(t *testing.T) {
	g := NewGomegaWithT(t)

	key := types.NamespacedName{
		Name:      mtName,
		Namespace: testNamespace,
	}
	created := &ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
		Spec: ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			VCSName:       vcsTest.ObjectMeta.Name,
			Image:         mtImage,
		},
	}

	g.Expect(created.DeepCopy().ValidatesAndSetDefaults(c)).NotTo(HaveOccurred())
	g.Expect(c.Create(context.TODO(), created)).NotTo(HaveOccurred())

	fetched := &ModelTraining{}
	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(created))

	updated := fetched.DeepCopy()
	updated.Spec.Image = mtNewImage
	g.Expect(c.Update(context.TODO(), updated)).NotTo(HaveOccurred())

	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(updated))
	g.Expect(fetched.Spec.Image).To(Equal(mtNewImage))

	// Test Delete
	g.Expect(c.Delete(context.TODO(), fetched)).NotTo(HaveOccurred())
	g.Expect(c.Get(context.TODO(), key, fetched)).To(HaveOccurred())
}

func TestMTDefaultValues(t *testing.T) {
	g := NewGomegaWithT(t)
	toolchainImage := "test/python:image"
	viper.SetDefault(legion.PythonToolchainImage, toolchainImage)
	mt := &ModelTraining{
		Spec: ModelTrainingSpec{
			VCSName:       vcsTest.ObjectMeta.Name,
			ToolchainType: legion.PythonToolchainName,
		},
	}

	_ = mt.ValidatesAndSetDefaults(c)
	g.Expect(*mt.Spec.Resources).To(Equal(defaultTrainingResources))
	g.Expect(mt.Spec.ModelFile).To(Equal(defaultModelFileName))
	g.Expect(mt.Spec.Reference).To(Equal(vcsTest.Spec.DefaultReference))
	g.Expect(mt.Spec.Image).To(Equal(toolchainImage))
}

func TestMTReference(t *testing.T) {
	g := NewGomegaWithT(t)

	mtExplicitReference := "test-ref"
	mt := &ModelTraining{
		Spec: ModelTrainingSpec{
			VCSName:   vcsTest.ObjectMeta.Name,
			Reference: mtExplicitReference,
		},
	}

	_ = mt.ValidatesAndSetDefaults(c)
	g.Expect(mt.Spec.Reference).To(Equal(mtExplicitReference))
}

func TestToolchainType(t *testing.T) {
	g := NewGomegaWithT(t)

	mt := &ModelTraining{
		Spec: ModelTrainingSpec{
			ToolchainType: "not-exists",
		},
	}

	err := mt.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring("Can't find not-exists toolchain"))
}

func TestVcsNotExists(t *testing.T) {
	g := NewGomegaWithT(t)
	toolchainImage := "test/python:image"
	viper.SetDefault(legion.PythonToolchainImage, toolchainImage)
	mt := &ModelTraining{
		Spec: ModelTrainingSpec{
			VCSName: "not-exists",
		},
	}

	err := mt.ValidatesAndSetDefaults(c)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring("vcscredentials.legion.legion-platform.org \"not-exists\" not found"))
}
