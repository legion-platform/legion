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

package deployment_test

import (
	"bytes"
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	dep_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment"
	dep_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	dep_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/deployment"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"net/http"
	"net/http/httptest"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"strings"
	"testing"
)

const (
	mrId  = "test-mr"
	mrId1 = "test-mr1"
	mrId2 = "test-mr2"
	mrUrl = "/test/url"
)

type ModelRouteSuite struct {
	suite.Suite
	g         *GomegaWithT
	server    *gin.Engine
	mdStorage dep_storage.Storage
}

func (s *ModelRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.mdStorage = dep_k8s_storage.NewStorageWithOptions(testNamespace, mgr.GetClient(), metav1.DeletePropagationBackground)
	dep_route.ConfigureRoutes(v1Group, s.mdStorage)

	err = s.mdStorage.CreateModelDeployment(&deployment.ModelDeployment{
		Id: mdId1,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			MinReplicas:                &mdMinReplicas,
			MaxReplicas:                &mdMaxReplicas,
			LivenessProbeInitialDelay:  &mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: &mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
			Resources:                  mdResources,
			RoleName:                   &mdRoleName,
		},
	})
	if err != nil {
		panic(err)
	}

	err = s.mdStorage.CreateModelDeployment(&deployment.ModelDeployment{
		Id: mdId2,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			MinReplicas:                &mdMinReplicas,
			MaxReplicas:                &mdMaxReplicas,
			LivenessProbeInitialDelay:  &mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: &mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
			Resources:                  mdResources,
			RoleName:                   &mdRoleName,
		},
	})
	if err != nil {
		panic(err)
	}
}

func (s *ModelRouteSuite) TearDownSuite() {
	for _, mdId := range []string{mdId1, mdId2} {
		if err := s.mdStorage.DeleteModelDeployment(mdId); err != nil && !errors.IsNotFound(err) {
			panic(err)
		}
	}
}

func (s *ModelRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelRouteSuite) TearDownTest() {
	for _, mdId := range []string{mrId, mrId1, mrId2} {
		if err := s.mdStorage.DeleteModelRoute(mdId); err != nil && !errors.IsNotFound(err) {
			panic(err)
		}
	}
}

func newStubMr() *deployment.ModelRoute {
	return &deployment.ModelRoute{
		Id: mrId,
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix: mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   mdId1,
					Weight: &dep_route.MaxWeight,
				},
			},
		},
	}
}

func TestModelRouteSuite(t *testing.T) {
	suite.Run(t, new(ModelRouteSuite))
}

func (s *ModelRouteSuite) TestGetMR() {
	mr := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(mr)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(dep_route.GetModelRouteUrl, ":id", mrId, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Spec).Should(Equal(mr.Spec))
}

func (s *ModelRouteSuite) TestGetMRNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(dep_route.GetModelRouteUrl, ":id", "not-found", -1),
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

func (s *ModelRouteSuite) TestGetAllModelRoutes() {
	conn := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(conn)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		dep_route.GetAllModelRouteUrl,
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	s.g.Expect(result[0].Id).Should(Equal(conn.Id))
	s.g.Expect(result[0].Spec).Should(Equal(conn.Spec))
}

func (s *ModelRouteSuite) TestGetAllEmptyModelRoutes() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		dep_route.GetAllModelRouteUrl,
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(0))
}

func (s *ModelRouteSuite) TestGetAllModelRoutesPaging() {
	mr1 := newStubMr()
	mr1.Id = mrId1
	s.g.Expect(s.mdStorage.CreateModelRoute(mr1)).NotTo(HaveOccurred())

	mr2 := newStubMr()
	mr2.Id = mrId2
	s.g.Expect(s.mdStorage.CreateModelRoute(mr2)).NotTo(HaveOccurred())

	connNames := map[string]interface{}{mrId1: nil, mrId2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelRouteUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "0")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	delete(connNames, result[0].Id)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, dep_route.GetAllModelRouteUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "1")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	delete(connNames, result[0].Id)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, dep_route.GetAllModelRouteUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query = req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "2")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(0))
	s.g.Expect(result).Should(BeEmpty())
}

func (s *ModelRouteSuite) TestCreateMR() {
	mrEntity := newStubMr()

	mrEntityBody, err := json.Marshal(mrEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelRouteUrl, bytes.NewReader(mrEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mrResponse deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &mrResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(mrResponse.Id).To(Equal(mrEntity.Id))
	s.g.Expect(mrResponse.Spec).To(Equal(mrEntity.Spec))

	mr, err := s.mdStorage.GetModelRoute(mrId)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mr.Id).To(Equal(mrEntity.Id))
	s.g.Expect(mr.Spec).To(Equal(mrEntity.Spec))
}

func (s *ModelRouteSuite) TestCreateDuplicateMR() {
	mr := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(mr)).NotTo(HaveOccurred())

	mrEntityBody, err := json.Marshal(mr)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelRouteUrl, bytes.NewReader(mrEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ModelRouteSuite) TestValidateCreateMR() {
	mr := newStubMr()
	mr.Spec.UrlPrefix = ""

	mrEntity, err := json.Marshal(mr)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelRouteUrl, bytes.NewReader(mrEntity))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).Should(ContainSubstring(dep_route.UrlPrefixEmptyErrorMessage))
}

func (s *ModelRouteSuite) TestUpdateMR() {
	mr := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(mr)).NotTo(HaveOccurred())

	newUrl := "/new/url"
	mrEntity := newStubMr()
	mrEntity.Spec.UrlPrefix = newUrl

	mrEntityBody, err := json.Marshal(mrEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelRouteUrl, bytes.NewReader(mrEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mrResponse deployment.ModelRoute
	err = json.Unmarshal(w.Body.Bytes(), &mrResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mrResponse.Id).To(Equal(mrEntity.Id))
	s.g.Expect(mrResponse.Spec).To(Equal(mrEntity.Spec))

	mr, err = s.mdStorage.GetModelRoute(mrId)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mr.Id).To(Equal(mrEntity.Id))
	s.g.Expect(mr.Spec).To(Equal(mrEntity.Spec))
}

func (s *ModelRouteSuite) TestUpdateMRNotFound() {
	mrEntity := newStubMr()

	mrEntityBody, err := json.Marshal(mrEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelRouteUrl, bytes.NewReader(mrEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ModelRouteSuite) TestValidateUpdateMR() {
	mr := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(mr)).NotTo(HaveOccurred())

	mr.Spec.UrlPrefix = ""
	connEntityBody, err := json.Marshal(mr)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelRouteUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).Should(ContainSubstring(dep_route.UrlPrefixEmptyErrorMessage))
}

func (s *ModelRouteSuite) TestDeleteMR() {
	mr := newStubMr()
	s.g.Expect(s.mdStorage.CreateModelRoute(mr)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(dep_route.DeleteModelRouteUrl, ":id", mrId, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	mrList, err := s.mdStorage.GetModelRouteList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mrList).To(HaveLen(0))
}

func (s *ModelRouteSuite) TestDeleteMRNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(dep_route.DeleteModelRouteUrl, ":id", mrId, -1),
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
