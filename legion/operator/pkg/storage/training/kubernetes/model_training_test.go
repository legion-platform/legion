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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"testing"

	. "github.com/onsi/gomega"
)

const (
	mtId            = "foo"
	modelName       = "test-model-name"
	modelVersion    = "test-model-version"
	newModelName    = "new-test-model-name"
	newModelVersion = "new-test-model-version"
)

// TODO: Add more tests
func TestStorageModelTraining(t *testing.T) {
	g := NewGomegaWithT(t)

	created := &training.ModelTraining{
		Id: mtId,
		Spec: v1alpha1.ModelTrainingSpec{
			Model: v1alpha1.ModelIdentity{
				Name:    modelName,
				Version: modelVersion,
			},
		},
	}

	g.Expect(c.CreateModelTraining(created)).NotTo(HaveOccurred())

	fetched, err := c.GetModelTraining(mtId)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(created.Id))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := &training.ModelTraining{
		Id: mtId,
		Spec: v1alpha1.ModelTrainingSpec{
			Model: v1alpha1.ModelIdentity{
				Name:    newModelName,
				Version: newModelVersion,
			},
		},
	}
	g.Expect(c.UpdateModelTraining(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetModelTraining(mtId)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(updated.Id))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.Model.Name).To(Equal(newModelName))
	g.Expect(fetched.Spec.Model.Version).To(Equal(newModelVersion))

	g.Expect(c.DeleteModelTraining(mtId)).NotTo(HaveOccurred())
	_, err = c.GetModelTraining(mtId)
	g.Expect(err).To(HaveOccurred())
}
