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
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
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
	"net/url"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"strings"
	"testing"
)

type ModelTrainingRouteSuite struct {
	suite.Suite
	g           *GomegaWithT
	server      *gin.Engine
	mtStorage   mt_storage.Storage
	connStorage conn_storage.Storage
}

func (s *ModelTrainingRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.mtStorage = mt_k8s_storage.NewStorage(testNamespace, testNamespace, mgr.GetClient(), nil)
	s.connStorage = conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient())
	train_route.ConfigureRoutes(v1Group, s.mtStorage, s.connStorage)

	// Create the connection that will be used as the vcs param for a training.
	if err := s.connStorage.CreateConnection(&connection.Connection{
		Id: testMtVCSId,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			Reference: testVcsReference,
		},
	}); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	// Create the toolchain integration that will be used for a training.
	if err := s.mtStorage.CreateToolchainIntegration(&training.ToolchainIntegration{
		Id: testToolchainIntegrationId,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			DefaultImage: testToolchainMtImage,
		},
	}); err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}
}

func (s *ModelTrainingRouteSuite) TearDownSuite() {
	if err := s.mtStorage.DeleteToolchainIntegration(testToolchainIntegrationId); err != nil {
		panic(err)
	}

	if err := s.connStorage.DeleteConnection(testMtVCSId); err != nil {
		panic(err)
	}
}

func (s *ModelTrainingRouteSuite) TearDownTest() {
	for _, mpId := range []string{testMtId, testMtId1, testMtId2} {
		if err := s.mtStorage.DeleteModelTraining(mpId); err != nil && !errors.IsNotFound(err) {
			// If a model training is not found then it was not created during a test case
			// All other errors propagate as a panic
			panic(err)
		}
	}
}

func (s *ModelTrainingRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelTrainingRouteSuite) newMultipleMtStubs() []*training.ModelTraining {
	mt1 := newMtStub()
	mt1.Id = testMtId1
	mt1.Spec.Model.Version = testModelVersion1
	s.g.Expect(s.mtStorage.CreateModelTraining(mt1)).NotTo(HaveOccurred())

	mt2 := newMtStub()
	mt2.Id = testMtId2
	mt2.Spec.Model.Version = testModelVersion2
	s.g.Expect(s.mtStorage.CreateModelTraining(mt2)).NotTo(HaveOccurred())

	return []*training.ModelTraining{mt1, mt2}
}

func TestModelTrainingRouteSuite(t *testing.T) {
	suite.Run(t, new(ModelTrainingRouteSuite))
}

func newMtStub() *training.ModelTraining {
	return &training.ModelTraining{
		Id: testMtId,
		Spec: v1alpha1.ModelTrainingSpec{
			Model: v1alpha1.ModelIdentity{
				Name:                 testModelName,
				Version:              testModelVersion1,
				ArtifactNameTemplate: train_route.DefaultArtifactOutputTemplate,
			},
			Toolchain:  testToolchainIntegrationId,
			Entrypoint: testMtEntrypoint,
			VCSName:    testMtVCSId,
			Image:      testMtImage,
			Reference:  testMtReference,
			Resources:  &train_route.DefaultTrainingResources,
		},
	}
}

func (s *ModelTrainingRouteSuite) TestGetMT() {
	mt := newMtStub()
	s.g.Expect(s.mtStorage.CreateModelTraining(mt)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, strings.Replace(train_route.GetModelTrainingUrl, ":id", mt.Id, -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Spec).Should(Equal(mt.Spec))
}

func (s *ModelTrainingRouteSuite) TestGetMTNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, strings.Replace(train_route.GetModelTrainingUrl, ":id", "not-present", -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelTrainingRouteSuite) TestGetAllMTEmptyResult() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllModelTrainingUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mtResponse []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &mtResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mtResponse).Should(HaveLen(0))
}

func (s *ModelTrainingRouteSuite) TestGetAllMT() {
	s.newMultipleMtStubs()
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllModelTrainingUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, mt := range result {
		s.g.Expect(mt.Id).To(Or(Equal(testMtId1), Equal(testMtId2)))
	}
}

func (s *ModelTrainingRouteSuite) TestGetAllMTPaging() {
	s.newMultipleMtStubs()
	trainingNames := map[string]interface{}{testMtId1: nil, testMtId2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, train_route.GetAllModelTrainingUrl, nil)
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
	delete(trainingNames, trainings[0].Id)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, train_route.GetAllModelTrainingUrl, nil)
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
	delete(trainingNames, trainings[0].Id)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, train_route.GetAllModelTrainingUrl, nil)
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

func (s *ModelTrainingRouteSuite) TestGetAllMTByModelName() {
	s.newMultipleMtStubs()

	params := url.Values{}
	params.Add(testModelNameFilter, testModelName)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/model/training?%s", params.Encode()), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, mt := range result {
		s.g.Expect(mt.Id).To(Or(Equal(testMtId1), Equal(testMtId2)))
	}
}

func (s *ModelTrainingRouteSuite) TestGetAllMTByModelVersion() {
	s.newMultipleMtStubs()

	params := url.Values{}
	params.Add(testModelVersionFilter, testModelVersion1)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("%s?%s", train_route.GetAllModelTrainingUrl, params.Encode()), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	s.g.Expect(result[0].Spec.Model.Name).To(Equal(testModelName))
	s.g.Expect(result[0].Spec.Model.Version).To(Equal(testModelVersion1))
}

func (s *ModelTrainingRouteSuite) TestGetAllMTByWrongModelVersion() {
	s.newMultipleMtStubs()

	params := url.Values{}
	params.Add(testModelVersionFilter, "wrong-version")

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("%s?%s", train_route.GetAllModelTrainingUrl, params.Encode()), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(0))
}

func (s *ModelTrainingRouteSuite) TestCreateMT() {
	initialMT := newMtStub()

	mtEntityBody, err := json.Marshal(initialMT)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mtResponse training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &mtResponse)

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(mtResponse.Id).Should(Equal(initialMT.Id))
	s.g.Expect(mtResponse.Spec).Should(Equal(initialMT.Spec))

	mt, err := s.mtStorage.GetModelTraining(testMtId)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mt.Id).Should(Equal(initialMT.Id))
	s.g.Expect(mt.Spec).Should(Equal(initialMT.Spec))
}

func (s *ModelTrainingRouteSuite) TestCreateMTCheckValidation() {
	initialMT := training.ModelTraining{
		Id: testModelName,
	}

	mtEntityBody, err := json.Marshal(initialMT)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var messageResponse routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &messageResponse)

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(messageResponse.Message).Should(ContainSubstring(train_route.ValidationMtErrorMessage))
}

func (s *ModelTrainingRouteSuite) TestCreateDuplicateMT() {
	mt := newMtStub()

	s.g.Expect(s.mtStorage.CreateModelTraining(mt)).NotTo(HaveOccurred())

	mtEntityBody, err := json.Marshal(mt)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, train_route.CreateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ModelTrainingRouteSuite) TestUpdateMT() {
	mt := newMtStub()
	s.g.Expect(s.mtStorage.CreateModelTraining(mt)).NotTo(HaveOccurred())

	newMt := &training.ModelTraining{
		Id:   mt.Id,
		Spec: mt.Spec,
	}
	newMt.Spec.Entrypoint = "new-entrypoint"

	mtEntityBody, err := json.Marshal(newMt)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mtResponse training.ModelTraining
	err = json.Unmarshal(w.Body.Bytes(), &mtResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mtResponse.Id).Should(Equal(newMt.Id))
	s.g.Expect(mtResponse.Spec).Should(Equal(newMt.Spec))

	mt, err = s.mtStorage.GetModelTraining(testMtId)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mt.Spec).To(Equal(newMt.Spec))
}

func (s *ModelTrainingRouteSuite) TestUpdateMTCheckValidation() {
	mt := newMtStub()
	s.g.Expect(s.mtStorage.CreateModelTraining(mt)).NotTo(HaveOccurred())

	newMt := &training.ModelTraining{
		Id:   mt.Id,
		Spec: v1alpha1.ModelTrainingSpec{},
	}

	mtEntityBody, err := json.Marshal(newMt)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mtResponse routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &mtResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(mtResponse.Message).Should(ContainSubstring(train_route.ValidationMtErrorMessage))
}

func (s *ModelTrainingRouteSuite) TestUpdateMTNotFound() {
	newMt := newMtStub()

	mtEntityBody, err := json.Marshal(newMt)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, train_route.UpdateModelTrainingUrl, bytes.NewReader(mtEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelTrainingRouteSuite) TestDeleteMT() {
	mt := newMtStub()
	s.g.Expect(s.mtStorage.CreateModelTraining(mt)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, strings.Replace(train_route.DeleteModelTrainingUrl, ":id", mt.Id, -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	mtList, err := s.mtStorage.GetModelTrainingList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mtList).To(HaveLen(0))
}

func (s *ModelTrainingRouteSuite) TestDeleteMTNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, strings.Replace(train_route.DeleteModelTrainingUrl, ":id", "not-found", -1), nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}
