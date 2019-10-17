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
	"bytes"
	"context"
	"encoding/json"
	"github.com/gin-gonic/gin"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	conn_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/kubernetes"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	pack_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"net/http"
	"net/http/httptest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"strings"
	"testing"
)

var (
	mpIDRoute           = "test-id"
	piIDMpRoute         = "pi-id"
	piEntrypointMpRoute = "/usr/bin/test"
	piImageMpRoute      = "test:image"
)

type ModelPackagingRouteSuite struct {
	suite.Suite
	g            *GomegaWithT
	server       *gin.Engine
	mpRepository mp_repository.Repository
	k8sClient    client.Client
}

func (s *ModelPackagingRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.k8sClient = mgr.GetClient()
	s.mpRepository = mp_k8s_repository.NewRepository(testNamespace, testNamespace, s.k8sClient, nil)
	pack_route.ConfigureRoutes(v1Group, s.mpRepository, conn_k8s_repository.NewRepository(testNamespace, mgr.GetClient()))

	err = s.mpRepository.CreatePackagingIntegration(&packaging.PackagingIntegration{
		ID: piIDMpRoute,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   piEntrypointMpRoute,
			DefaultImage: piImageMpRoute,
			Schema:       packaging.Schema{},
		},
	})
	if err != nil {
		panic(err)
	}
}

func (s *ModelPackagingRouteSuite) TearDownSuite() {
	if err := s.mpRepository.DeletePackagingIntegration(piIDMpValid); err != nil {
		panic(err)
	}
}

func (s *ModelPackagingRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelPackagingRouteSuite) TearDownTest() {
	for _, mpID := range []string{mpIDRoute, testMpID1, testMpID2} {
		if err := s.mpRepository.DeleteModelPackaging(mpID); err != nil && !errors.IsNotFound(err) {
			// If a model packaging is not found then it was not created during a test case
			// All other errors propagate as a panic
			panic(err)
		}
	}
}

func newModelPackaging() *packaging.ModelPackaging {
	return &packaging.ModelPackaging{
		ID: mpIDRoute,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName:    mpArtifactName,
			IntegrationName: piIDMpRoute,
			Image:           mpImage,
			Resources:       pack_route.DefaultPackagingResources,
		},
	}
}

func (s *ModelPackagingRouteSuite) createModelPackagings() []*packaging.ModelPackaging {
	mp1 := newModelPackaging()
	mp1.ID = testMpID1
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp1)).NotTo(HaveOccurred())

	mp2 := newModelPackaging()
	mp2.ID = testMpID2
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp2)).NotTo(HaveOccurred())

	return []*packaging.ModelPackaging{mp1, mp2}
}

func TestModelPackagingRouteSuite(t *testing.T) {
	suite.Run(t, new(ModelPackagingRouteSuite))
}

func (s *ModelPackagingRouteSuite) TestGetMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(pack_route.GetModelPackagingURL, ":id", mp.ID, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Spec).Should(Equal(mp.Spec))
}

func (s *ModelPackagingRouteSuite) TestGetMPNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(pack_route.GetModelPackagingURL, ":id", "not-found", -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelPackagingRouteSuite) TestGetAllMPEmptyResult() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mpResponse []packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &mpResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mpResponse).Should(HaveLen(0))
}

func (s *ModelPackagingRouteSuite) TestGetAllMP() {
	s.createModelPackagings()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, mp := range result {
		s.g.Expect(mp.ID).To(Or(Equal(testMpID1), Equal(testMpID2)))
	}
}

func (s *ModelPackagingRouteSuite) TestGetAllMTPaging() {
	s.createModelPackagings()

	mpNames := map[string]interface{}{testMpID1: nil, testMpID2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "0")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var trainings []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &trainings)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(trainings).Should(HaveLen(1))
	delete(mpNames, trainings[0].ID)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "1")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &trainings)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(trainings).Should(HaveLen(1))
	delete(mpNames, trainings[0].ID)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "2")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &trainings)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(trainings).Should(HaveLen(0))
	s.g.Expect(trainings).Should(BeEmpty())
}

func (s *ModelPackagingRouteSuite) TestCreateMP() {
	mpEntity := newModelPackaging()

	mpEntityBody, err := json.Marshal(mpEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, pack_route.CreateModelPackagingURL, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mpResponse packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &mpResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(mpResponse.ID).Should(Equal(mpEntity.ID))
	s.g.Expect(mpResponse.Spec).Should(Equal(mpEntity.Spec))

	mp, err := s.mpRepository.GetModelPackaging(mpIDRoute)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mp.Spec).To(Equal(mpEntity.Spec))
}

func (s *ModelPackagingRouteSuite) TestCreateDuplicateMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	mpEntityBody, err := json.Marshal(mp)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, pack_route.CreateModelPackagingURL, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ModelPackagingRouteSuite) TestUpdateMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	updatedMp := newModelPackaging()
	updatedMp.Spec.Image += "123"

	mpEntityBody, err := json.Marshal(updatedMp)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, pack_route.UpdateModelPackagingURL, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mpResponse packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &mpResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mpResponse.ID).Should(Equal(updatedMp.ID))
	s.g.Expect(mpResponse.Spec).Should(Equal(updatedMp.Spec))

	mp, err = s.mpRepository.GetModelPackaging(mpIDRoute)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mp.Spec).To(Equal(updatedMp.Spec))
}

func (s *ModelPackagingRouteSuite) TestUpdateMPNotFound() {
	mpEntity := newModelPackaging()

	mpEntityBody, err := json.Marshal(mpEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, pack_route.UpdateModelPackagingURL, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelPackagingRouteSuite) TestDeleteMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpRepository.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(pack_route.DeleteModelPackagingURL, ":id", mp.ID, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	mpList, err := s.mpRepository.GetModelPackagingList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mpList).To(HaveLen(0))
}

func (s *ModelPackagingRouteSuite) TestDeleteMPNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(pack_route.DeleteModelPackagingURL, ":id", "some-mp-id", -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelPackagingRouteSuite) TestSavingMPResult() {
	resultCM := &corev1.ConfigMap{
		ObjectMeta: v1.ObjectMeta{
			Name:      legion.GeneratePackageResultCMName(mpIDRoute),
			Namespace: testNamespace,
		},
	}
	s.g.Expect(s.k8sClient.Create(context.TODO(), resultCM)).NotTo(HaveOccurred())
	defer s.k8sClient.Delete(context.TODO(), resultCM)

	expectedMPResult := []legionv1alpha1.ModelPackagingResult{
		{
			Name:  "test-name-1",
			Value: "test-value-1",
		},
		{
			Name:  "test-name-2",
			Value: "test-value-2",
		},
	}
	expectedMPResultBody, err := json.Marshal(expectedMPResult)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodPut,
		strings.Replace(pack_route.SaveModelPackagingResultURL, ":id", mpIDRoute, -1),
		bytes.NewReader(expectedMPResultBody),
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	result := []legionv1alpha1.ModelPackagingResult{}
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(expectedMPResult).Should(Equal(result))

	result, err = s.mpRepository.GetModelPackagingResult(mpIDRoute)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(expectedMPResult).To(Equal(result))
}
