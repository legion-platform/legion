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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"k8s.io/apimachinery/pkg/api/errors"
	"testing"

	. "github.com/onsi/gomega"
)

const (
	mpImage    = "test:new_image"
	mpNewImage = "test:new_image"
	mpType     = "test-type"
	mpId       = "mp1"
)

var (
	mpArtifactName = "someArtifactName"
	mpArguments    = map[string]interface{}{
		"key-1": "value-1",
		"key-2": float64(5),
		"key-3": true,
	}
	mpTargets = []v1alpha1.Target{
		{
			Name:           "test",
			ConnectionName: "test-conn",
		},
	}
)

func TestStorageModelPackaging(t *testing.T) {
	g := NewGomegaWithT(t)

	created := &packaging.ModelPackaging{
		Id: mpId,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName:    mpArtifactName,
			IntegrationName: mpType,
			Image:           mpImage,
			Arguments:       mpArguments,
			Targets:         mpTargets,
		},
	}

	g.Expect(c.CreateModelPackaging(created)).NotTo(HaveOccurred())

	fetched, err := c.GetModelPackaging(mpId)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(created.Id))
	g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := fetched
	updated.Spec.Image = mpNewImage
	g.Expect(c.UpdateModelPackaging(updated)).NotTo(HaveOccurred())

	fetched, err = c.GetModelPackaging(mpId)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(fetched.Id).To(Equal(updated.Id))
	g.Expect(fetched.Spec).To(Equal(updated.Spec))
	g.Expect(fetched.Spec.Image).To(Equal(mpNewImage))

	g.Expect(c.DeleteModelPackaging(mpId)).NotTo(HaveOccurred())
	_, err = c.GetModelPackaging(mpId)
	g.Expect(err).To(HaveOccurred())
	g.Expect(errors.IsNotFound(err)).Should(BeTrue())
}
