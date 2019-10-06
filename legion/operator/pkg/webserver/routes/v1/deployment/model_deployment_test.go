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
	dep_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/deployment"
	dep_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/deployment/kubernetes"
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

var (
	mdID                    = "test-model-deployment"
	mdID1                   = "test-model-deployment1"
	mdID2                   = "test-model-deployment2"
	mdRoleName1             = "role-1"
	mdRoleName2             = "role-2"
	mdImage                 = "test/test:123"
	mdMinReplicas           = int32(1)
	mdMaxReplicas           = int32(2)
	mdLivenessInitialDelay  = int32(60)
	mdReadinessInitialDelay = int32(30)
)

var (
	mdAnnotations = map[string]string{"k1": "v1", "k2": "v2"}
	reqMem        = "111Mi"
	reqCPU        = "111m"
	limMem        = "222Mi"
	mdResources   = &legionv1alpha1.ResourceRequirements{
		Limits: &legionv1alpha1.ResourceList{
			CPU:    nil,
			Memory: &limMem,
		},
		Requests: &legionv1alpha1.ResourceList{
			CPU:    &reqCPU,
			Memory: &reqMem,
		},
	}
)

type ModelDeploymentRouteSuite struct {
	suite.Suite
	g            *GomegaWithT
	server       *gin.Engine
	mdRepository dep_repository.Repository
}

func (s *ModelDeploymentRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.mdRepository = dep_k8s_repository.NewRepositoryWithOptions(
		testNamespace, mgr.GetClient(), metav1.DeletePropagationBackground,
	)
	dep_route.ConfigureRoutes(v1Group, s.mdRepository)
}

func (s *ModelDeploymentRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ModelDeploymentRouteSuite) TearDownTest() {
	for _, currMdID := range []string{mdID, mdID1, mdID2} {
		if err := s.mdRepository.DeleteModelDeployment(currMdID); err != nil && !errors.IsNotFound(err) {
			panic(err)
		}
	}
}

func newStubMd() *deployment.ModelDeployment {
	return &deployment.ModelDeployment{
		ID: mdID,
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
	}
}

func (s *ModelDeploymentRouteSuite) newMultipleMds() []*deployment.ModelDeployment {
	md1 := newStubMd()
	md1.ID = mdID1
	md1.Spec.RoleName = &mdRoleName1
	s.g.Expect(s.mdRepository.CreateModelDeployment(md1)).NotTo(HaveOccurred())

	md2 := newStubMd()
	md2.ID = mdID2
	md2.Spec.RoleName = &mdRoleName2
	s.g.Expect(s.mdRepository.CreateModelDeployment(md2)).NotTo(HaveOccurred())

	return []*deployment.ModelDeployment{md1, md2}
}

func TestModelDeploymentRouteSuite(t *testing.T) {
	suite.Run(t, new(ModelDeploymentRouteSuite))
}

func (s *ModelDeploymentRouteSuite) TestGetMD() {
	md := newStubMd()
	s.g.Expect(s.mdRepository.CreateModelDeployment(md)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(dep_route.GetModelDeploymentURL, ":id", mdID, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(Equal(deployment.ModelDeployment{
		ID: md.ID, Spec: md.Spec, Status: &legionv1alpha1.ModelDeploymentStatus{},
	}))
}

func (s *ModelDeploymentRouteSuite) TestGetMDNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(dep_route.GetModelDeploymentURL, ":id", "not-found", -1),
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

func (s *ModelDeploymentRouteSuite) TestGetAllMDEmptyResult() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mdResponse []deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &mdResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mdResponse).Should(HaveLen(0))
}

func (s *ModelDeploymentRouteSuite) TestGetAllMD() {
	s.newMultipleMds()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))

	for _, md := range result {
		s.g.Expect(md.ID).To(Or(Equal(mdID1), Equal(mdID2)))
	}
}

func (s *ModelDeploymentRouteSuite) TestGetAllMdByRole() {
	mds := s.newMultipleMds()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("roleName", mdRoleName2)
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	s.g.Expect(result[0].ID).Should(Equal(mdID2))
	s.g.Expect(result[0].Spec).Should(Equal(mds[1].Spec))
}

func (s *ModelDeploymentRouteSuite) TestGetAllMdMultipleFiltersByRole() {
	s.newMultipleMds()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("roleName", mdRoleName1)
	query.Add("roleName", mdRoleName2)
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))
}

func (s *ModelDeploymentRouteSuite) TestGetAllMdPaging() {
	s.newMultipleMds()

	mdNames := map[string]interface{}{mdID1: nil, mdID2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "0")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	delete(mdNames, result[0].ID)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
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
	delete(mdNames, result[0].ID)

	// Return third empty page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, dep_route.GetAllModelDeploymentURL, nil)
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

func (s *ModelDeploymentRouteSuite) TestCreateMD() {
	mdEntity := newStubMd()
	mdEntityBody, err := json.Marshal(mdEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mdResponse deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &mdResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(mdEntity.ID).To(Equal(mdResponse.ID))
	s.g.Expect(mdEntity.Spec).To(Equal(mdResponse.Spec))

	md, err := s.mdRepository.GetModelDeployment(mdID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(md.Spec).To(Equal(mdEntity.Spec))
}

func (s *ModelDeploymentRouteSuite) TestCreateMDValidation() {
	mdEntity := newStubMd()
	mdEntity.Spec.Image = ""
	mdEntityBody, err := json.Marshal(mdEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).To(Equal(dep_route.EmptyImageErrorMessage))
}

func (s *ModelDeploymentRouteSuite) TestCreateDuplicateMD() {
	md := newStubMd()

	s.g.Expect(s.mdRepository.CreateModelDeployment(md)).NotTo(HaveOccurred())

	mdEntityBody, err := json.Marshal(md)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ModelDeploymentRouteSuite) TestUpdateMD() {
	md := newStubMd()
	s.g.Expect(s.mdRepository.CreateModelDeployment(md)).NotTo(HaveOccurred())

	newMaxReplicas := mdMaxReplicas + 1
	newMDLivenessIninitialDelay := mdLivenessInitialDelay + 1
	newMDReadinessInitialDelay := mdReadinessInitialDelay + 1

	mdEntity := newStubMd()
	mdEntity.Spec.MaxReplicas = &newMaxReplicas
	mdEntity.Spec.LivenessProbeInitialDelay = &newMDLivenessIninitialDelay
	mdEntity.Spec.ReadinessProbeInitialDelay = &newMDReadinessInitialDelay

	mdEntityBody, err := json.Marshal(mdEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var mdResponse deployment.ModelDeployment
	err = json.Unmarshal(w.Body.Bytes(), &mdResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(mdEntity.ID).To(Equal(mdResponse.ID))
	s.g.Expect(mdEntity.Spec).To(Equal(mdResponse.Spec))

	md, err = s.mdRepository.GetModelDeployment(mdID)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mdEntity.ID).To(Equal(md.ID))
	s.g.Expect(mdEntity.Spec).To(Equal(md.Spec))
}

func (s *ModelDeploymentRouteSuite) TestUpdateMDValidation() {
	md := newStubMd()
	s.g.Expect(s.mdRepository.CreateModelDeployment(md)).NotTo(HaveOccurred())

	mdEntity := newStubMd()
	mdEntity.Spec.Image = ""

	mdEntityBody, err := json.Marshal(mdEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).To(Equal(dep_route.EmptyImageErrorMessage))
}

func (s *ModelDeploymentRouteSuite) TestUpdateMDNotFound() {
	mdEntity := newStubMd()

	mdEntityBody, err := json.Marshal(mdEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, dep_route.UpdateModelDeploymentURL, bytes.NewReader(mdEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).To(ContainSubstring("not found"))
}

func (s *ModelDeploymentRouteSuite) TestDeleteMD() {
	md := newStubMd()
	s.g.Expect(s.mdRepository.CreateModelDeployment(md)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(dep_route.DeleteModelDeploymentURL, ":id", md.ID, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	mdList, err := s.mdRepository.GetModelDeploymentList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(mdList).To(HaveLen(0))
}

func (s *ModelDeploymentRouteSuite) TestDeleteMDNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(dep_route.DeleteModelDeploymentURL, ":id", "not-found", -1),
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
