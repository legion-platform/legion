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
	"context"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"testing"
)

const (
	mpImage    = "test:new_image"
	mpNewImage = "test:new_image"
	mpType     = "test-type"
	mpID       = "mp1"
)

var (
	mpArtifactName = "someArtifactName"
	mpArguments    = map[string]interface{}{
		"key-1": "value-1",
		"key-2": float64(5),
		"key-3": true,
	}
	mpTargets = []legionv1alpha1.Target{
		{
			Name:           "test",
			ConnectionName: "test-conn",
		},
	}
)

type MPRepositorySuite struct {
	suite.Suite
	g         *GomegaWithT
	k8sClient client.Client
	rep       mp_repository.Repository
}

func generateMPResultCM() *corev1.ConfigMap {
	return &corev1.ConfigMap{
		ObjectMeta: v1.ObjectMeta{
			Name:      legion.GeneratePackageResultCMName(mpID),
			Namespace: testNamespace,
		},
	}
}

func generateMP() *packaging.ModelPackaging {
	return &packaging.ModelPackaging{
		ID: mpID,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName:    mpArtifactName,
			IntegrationName: mpType,
			Image:           mpImage,
			Arguments:       mpArguments,
			Targets:         mpTargets,
		},
	}
}

func (s *MPRepositorySuite) SetupSuite() {
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

func (s *MPRepositorySuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *MPRepositorySuite) TearDownTest() {
	if err := s.rep.DeleteModelPackaging(mpID); err != nil && !errors.IsNotFound(err) {
		// If we get the panic that we have a test configuration problem
		panic(err)
	}
}

func TestSuiteMP(t *testing.T) {
	suite.Run(t, new(MPRepositorySuite))
}

func (s *MPRepositorySuite) TestModelPackagingRepository() {
	created := generateMP()

	s.g.Expect(s.rep.CreateModelPackaging(created)).NotTo(HaveOccurred())

	fetched, err := s.rep.GetModelPackaging(mpID)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(fetched.ID).To(Equal(created.ID))
	s.g.Expect(fetched.Spec).To(Equal(created.Spec))

	updated := fetched
	updated.Spec.Image = mpNewImage
	s.g.Expect(s.rep.UpdateModelPackaging(updated)).NotTo(HaveOccurred())

	fetched, err = s.rep.GetModelPackaging(mpID)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(fetched.ID).To(Equal(updated.ID))
	s.g.Expect(fetched.Spec).To(Equal(updated.Spec))
	s.g.Expect(fetched.Spec.Image).To(Equal(mpNewImage))

	s.g.Expect(s.rep.DeleteModelPackaging(mpID)).NotTo(HaveOccurred())
	_, err = s.rep.GetModelPackaging(mpID)
	s.g.Expect(err).To(HaveOccurred())
	s.g.Expect(errors.IsNotFound(err)).Should(BeTrue())
}

func (s *MPRepositorySuite) TestModelPackagingResult() {
	created := generateMP()
	s.g.Expect(s.rep.CreateModelPackaging(created)).NotTo(HaveOccurred())

	resultConfigMap := generateMPResultCM()
	err := s.k8sClient.Create(context.TODO(), resultConfigMap)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	defer s.k8sClient.Delete(context.TODO(), resultConfigMap)

	expectedPackagingResult := []legionv1alpha1.ModelPackagingResult{
		{
			Name:  "test-name-1",
			Value: "test-value-1",
		},
		{
			Name:  "test-name-2",
			Value: "test-value-2",
		},
	}
	err = s.rep.SaveModelPackagingResult(mpID, expectedPackagingResult)
	s.g.Expect(err).ShouldNot(HaveOccurred())

	results, err := s.rep.GetModelPackagingResult(mpID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(expectedPackagingResult).Should(Equal(results))
}

func (s *MPRepositorySuite) TestMPResultConfigMapNotFound() {
	created := generateMP()
	s.g.Expect(s.rep.CreateModelPackaging(created)).NotTo(HaveOccurred())

	expectedPackagingResult := []legionv1alpha1.ModelPackagingResult{
		{
			Name:  "test-name-1",
			Value: "test-value-1",
		},
		{
			Name:  "test-name-2",
			Value: "test-value-2",
		},
	}
	err := s.rep.SaveModelPackagingResult(mpID, expectedPackagingResult)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}

func (s *MPRepositorySuite) TestEmptyModelPackagingResult() {
	created := generateMP()
	s.g.Expect(s.rep.CreateModelPackaging(created)).NotTo(HaveOccurred())

	resultConfigMap := generateMPResultCM()
	err := s.k8sClient.Create(context.TODO(), resultConfigMap)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	defer s.k8sClient.Delete(context.TODO(), resultConfigMap)

	expectedPackagingResult := []legionv1alpha1.ModelPackagingResult{}
	err = s.rep.SaveModelPackagingResult(mpID, expectedPackagingResult)
	s.g.Expect(err).ShouldNot(HaveOccurred())

	results, err := s.rep.GetModelPackagingResult(mpID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(expectedPackagingResult).Should(Equal(results))
}
