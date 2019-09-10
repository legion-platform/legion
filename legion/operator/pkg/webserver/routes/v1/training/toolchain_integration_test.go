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
	"bytes"
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	conn_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	mt_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
	mt_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	train_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/training"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"k8s.io/apimachinery/pkg/api/errors"
	"net/http"
	"net/http/httptest"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"strings"
	"testing"
)

const (
	tiEntrypoint   = "test-entrypoint"
	tiDefaultImage = "test:image"
)

var (
	tiAdditionalEnvironments = map[string]string{
		"name-123": "value-456",
	}
)

type ToolchainIntegrationRouteSuite struct {
	suite.Suite
	g           *GomegaWithT
	server      *gin.Engine
	mtStorage   mt_storage.Storage
	connStorage conn_storage.Storage
}

func (s *ToolchainIntegrationRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.mtStorage = mt_k8s_storage.NewStorage(testNamespace, testNamespace, mgr.GetClient(), nil)
	s.connStorage = conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient())
	train_route.ConfigureRoutes(v1Group, s.mtStorage, s.connStorage)
}

func (s *ToolchainIntegrationRouteSuite) TearDownTest() {
	for _, mpId := range []string{testToolchainIntegrationId, testToolchainIntegrationId1, testToolchainIntegrationId2} {
		if err := s.mtStorage.DeleteToolchainIntegration(mpId); err != nil && !errors.IsNotFound(err) {
			// If a model training is not found then it was not created during a test case
			// All other errors propagate as a panic
			panic(err)
		}
	}
}

func (s *ToolchainIntegrationRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ToolchainIntegrationRouteSuite) newMultipleMtStubs() []*training.ToolchainIntegration {
	ti1 := newTiStub()
	ti1.Id = testToolchainIntegrationId1
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti1)).NotTo(HaveOccurred())

	ti2 := newTiStub()
	ti2.Id = testToolchainIntegrationId2
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti2)).NotTo(HaveOccurred())

	return []*training.ToolchainIntegration{ti1, ti2}
}

func TestToolchainIntegrationRouteSuite(t *testing.T) {
	suite.Run(t, new(ToolchainIntegrationRouteSuite))
}

func newTiStub() *training.ToolchainIntegration {
	return &training.ToolchainIntegration{
		Id: testToolchainIntegrationId,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			Entrypoint:             tiEntrypoint,
			DefaultImage:           tiDefaultImage,
			AdditionalEnvironments: tiAdditionalEnvironments,
		},
	}
}

func (s *ToolchainIntegrationRouteSuite) newMultipleTiStubs() []*training.ToolchainIntegration {
	ti1 := &training.ToolchainIntegration{
		Id: testToolchainIntegrationId1,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			DefaultImage: testToolchainMtImage,
		},
	}
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti1)).NotTo(HaveOccurred())

	ti2 := &training.ToolchainIntegration{
		Id: testToolchainIntegrationId2,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			DefaultImage: testToolchainMtImage,
		},
	}
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti2)).NotTo(HaveOccurred())

	return []*training.ToolchainIntegration{ti1, ti2}
}

func (s *ToolchainIntegrationRouteSuite) TestGetToolchainIntegration() {
	ti := newTiStub()
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, strings.Replace(train_route.GetToolchainIntegrationUrl, ":id", ti.Id, -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var tiResponse training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &tiResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(tiResponse.Id).Should(Equal(ti.Id))
	s.g.Expect(tiResponse.Spec).Should(Equal(ti.Spec))
}

func (s *ToolchainIntegrationRouteSuite) TestGetToolchainIntegrationNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, strings.Replace(train_route.GetToolchainIntegrationUrl, ":id", "not-found", -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ToolchainIntegrationRouteSuite) TestGetAllTiEmptyResult() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllToolchainIntegrationUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var tiResponse []training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &tiResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(tiResponse).Should(HaveLen(0))
}

func (s *ToolchainIntegrationRouteSuite) TestGetAllTi() {
	s.newMultipleTiStubs()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllToolchainIntegrationUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, ti := range result {
		s.g.Expect(ti.Id).To(Or(Equal(testToolchainIntegrationId1), Equal(testToolchainIntegrationId2)))
	}
}

func (s *ToolchainIntegrationRouteSuite) TestGetAllTiPaging() {
	s.newMultipleTiStubs()

	toolchainsNames := map[string]interface{}{testToolchainIntegrationId1: nil, testToolchainIntegrationId2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllToolchainIntegrationUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "0")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var toolchains []training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &toolchains)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(toolchains).Should(HaveLen(1))
	delete(toolchainsNames, toolchains[0].Id)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, train_route.GetAllToolchainIntegrationUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "1")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &toolchains)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(toolchains).Should(HaveLen(1))
	delete(toolchainsNames, toolchains[0].Id)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, train_route.GetAllToolchainIntegrationUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "2")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &toolchains)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(toolchains).Should(HaveLen(0))
	s.g.Expect(toolchains).Should(BeEmpty())
}

func (s *ToolchainIntegrationRouteSuite) TestCreateToolchainIntegration() {
	tiEntity := newTiStub()

	tiEntityBody, err := json.Marshal(tiEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateToolchainIntegrationUrl, bytes.NewReader(tiEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var tiResponse training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &tiResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(tiResponse.Id).Should(Equal(tiEntity.Id))
	s.g.Expect(tiResponse.Spec).Should(Equal(tiEntity.Spec))

	ti, err := s.mtStorage.GetToolchainIntegration(testToolchainIntegrationId)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(ti.Spec).To(Equal(tiEntity.Spec))
}

func (s *ToolchainIntegrationRouteSuite) TestCreateToolchainIntegrationValidation() {
	tiEntity := newTiStub()
	tiEntity.Spec.Entrypoint = ""

	tiEntityBody, err := json.Marshal(tiEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateToolchainIntegrationUrl, bytes.NewReader(tiEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var resultResponse routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &resultResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(resultResponse.Message).Should(ContainSubstring(train_route.ValidationTiErrorMessage))
}

func (s *ToolchainIntegrationRouteSuite) TestCreateDuplicateToolchainIntegration() {
	ti := newTiStub()

	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti)).NotTo(HaveOccurred())

	tiEntityBody, err := json.Marshal(ti)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateToolchainIntegrationUrl, bytes.NewReader(tiEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ToolchainIntegrationRouteSuite) TestUpdateToolchainIntegration() {
	ti := newTiStub()
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti)).NotTo(HaveOccurred())

	updatedTi := newTiStub()
	updatedTi.Spec.Entrypoint = "new-entrypoint"

	tiEntityBody, err := json.Marshal(updatedTi)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateToolchainIntegrationUrl, bytes.NewReader(tiEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var tiResponse training.ToolchainIntegration
	err = json.Unmarshal(w.Body.Bytes(), &tiResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(tiResponse.Id).Should(Equal(updatedTi.Id))
	s.g.Expect(tiResponse.Spec).Should(Equal(updatedTi.Spec))

	ti, err = s.mtStorage.GetToolchainIntegration(testToolchainIntegrationId)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(ti.Spec).To(Equal(updatedTi.Spec))
}

func (s *ToolchainIntegrationRouteSuite) TestUpdateToolchainIntegrationValidation() {
	ti := newTiStub()
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti)).NotTo(HaveOccurred())

	updatedTi := newTiStub()
	updatedTi.Spec.Entrypoint = ""

	tiEntityBody, err := json.Marshal(updatedTi)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateToolchainIntegrationUrl, bytes.NewReader(tiEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var resultResponse routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &resultResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(resultResponse.Message).Should(ContainSubstring(train_route.ValidationTiErrorMessage))
}

func (s *ToolchainIntegrationRouteSuite) TestUpdateToolchainIntegrationNotFound() {
	ti := newTiStub()

	tiBody, err := json.Marshal(ti)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateToolchainIntegrationUrl, bytes.NewReader(tiBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var response routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &response)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(response.Message).Should(ContainSubstring("not found"))
}

func (s *ToolchainIntegrationRouteSuite) TestDeleteToolchainIntegration() {
	ti := newTiStub()
	s.g.Expect(s.mtStorage.CreateToolchainIntegration(ti)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, strings.Replace(train_route.DeleteToolchainIntegrationUrl, ":id", ti.Id, -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	tiList, err := s.mtStorage.GetToolchainIntegrationList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(tiList).To(HaveLen(0))
}

func (s *ToolchainIntegrationRouteSuite) TestDeleteToolchainIntegrationNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, strings.Replace(train_route.DeleteToolchainIntegrationUrl, ":id", "not-found", -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}
