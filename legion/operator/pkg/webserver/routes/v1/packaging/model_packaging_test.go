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
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	conn_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"k8s.io/apimachinery/pkg/api/errors"
	"strings"

	mp_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging/kubernetes"
	pack_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	"sigs.k8s.io/controller-runtime/pkg/manager"

	"net/http"
	"net/http/httptest"
	"testing"
)

var (
	mpIdRoute           = "test-id"
	piIdMpRoute         = "pi-id"
	piEntrypointMpRoute = "/usr/bin/test"
	piImageMpRoute      = "test:image"
)

type ModelPackagingRouteSuite struct {
	suite.Suite
	g         *GomegaWithT
	server    *gin.Engine
	mpStorage mp_storage.Storage
}

func (s *ModelPackagingRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.mpStorage = mp_k8s_storage.NewStorage(testNamespace, testNamespace, mgr.GetClient(), nil)
	pack_route.ConfigureRoutes(v1Group, s.mpStorage, conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient()))

	err = s.mpStorage.CreatePackagingIntegration(&packaging.PackagingIntegration{
		Id: piIdMpRoute,
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
	if err := s.mpStorage.DeletePackagingIntegration(piIdMpValid); err != nil {
		panic(err)
	}
}

func (s *ModelPackagingRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelPackagingRouteSuite) TearDownTest() {
	for _, mpId := range []string{mpIdRoute, testMpId1, testMpId2} {
		if err := s.mpStorage.DeleteModelPackaging(mpId); err != nil && !errors.IsNotFound(err) {
			// If a model packaging is not found then it was not created during a test case
			// All other errors propagate as a panic
			panic(err)
		}
	}
}

func newModelPackaging() *packaging.ModelPackaging {
	return &packaging.ModelPackaging{
		Id: mpIdRoute,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName:    mpArtifactName,
			IntegrationName: piIdMpRoute,
			Image:           mpImage,
		},
	}
}

func (s *ModelPackagingRouteSuite) createModelPackagings() []*packaging.ModelPackaging {
	mp1 := newModelPackaging()
	mp1.Id = testMpId1
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp1)).NotTo(HaveOccurred())

	mp2 := newModelPackaging()
	mp2.Id = testMpId2
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp2)).NotTo(HaveOccurred())

	return []*packaging.ModelPackaging{mp1, mp2}
}

func TestModelPackagingRouteSuite(t *testing.T) {
	suite.Run(t, new(ModelPackagingRouteSuite))
}

func (s *ModelPackagingRouteSuite) TestGetMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(pack_route.GetModelPackagingUrl, ":id", mp.Id, -1),
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
		strings.Replace(pack_route.GetModelPackagingUrl, ":id", "not-found", -1),
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
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingUrl, nil)
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
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, mp := range result {
		s.g.Expect(mp.Id).To(Or(Equal(testMpId1), Equal(testMpId2)))
	}
}

func (s *ModelPackagingRouteSuite) TestGetAllMTPaging() {
	s.createModelPackagings()

	mpNames := map[string]interface{}{testMpId1: nil, testMpId2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingUrl, nil)
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
	delete(mpNames, trainings[0].Id)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingUrl, nil)
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
	delete(mpNames, trainings[0].Id)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, pack_route.GetAllModelPackagingUrl, nil)
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
	req, err := http.NewRequest(http.MethodPost, pack_route.CreateModelPackagingUrl, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mpResponse packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &mpResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(mpResponse.Id).Should(Equal(mpEntity.Id))
	s.g.Expect(mpResponse.Spec).Should(Equal(mpEntity.Spec))

	mp, err := s.mpStorage.GetModelPackaging(mpIdRoute)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mp.Spec).To(Equal(mpEntity.Spec))
}

func (s *ModelPackagingRouteSuite) TestCreateDuplicateMP() {
	mp := newModelPackaging()
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	mpEntityBody, err := json.Marshal(mp)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, pack_route.CreateModelPackagingUrl, bytes.NewReader(mpEntityBody))
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
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	updatedMp := newModelPackaging()
	updatedMp.Spec.Image = updatedMp.Spec.Image + "123"

	mpEntityBody, err := json.Marshal(updatedMp)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, pack_route.UpdateModelPackagingUrl, bytes.NewReader(mpEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mpResponse packaging.ModelPackaging
	err = json.Unmarshal(w.Body.Bytes(), &mpResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mpResponse.Id).Should(Equal(updatedMp.Id))
	s.g.Expect(mpResponse.Spec).Should(Equal(updatedMp.Spec))

	mp, err = s.mpStorage.GetModelPackaging(mpIdRoute)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mp.Spec).To(Equal(updatedMp.Spec))
}

func (s *ModelPackagingRouteSuite) TestUpdateMPNotFound() {
	mpEntity := newModelPackaging()

	mpEntityBody, err := json.Marshal(mpEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, pack_route.UpdateModelPackagingUrl, bytes.NewReader(mpEntityBody))
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
	s.g.Expect(s.mpStorage.CreateModelPackaging(mp)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(pack_route.DeleteModelPackagingUrl, ":id", mp.Id, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	mpList, err := s.mpStorage.GetModelPackagingList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mpList).To(HaveLen(0))
}

func (s *ModelPackagingRouteSuite) TestDeleteMPNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(pack_route.DeleteModelPackagingUrl, ":id", "some-mp-id", -1),
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
