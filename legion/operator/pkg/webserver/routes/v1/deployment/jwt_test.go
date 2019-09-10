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
	"encoding/base64"
	"encoding/json"
	"github.com/gin-gonic/gin"
	md_config "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/deployment"
	dep_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/deployment"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	"github.com/stretchr/testify/suite"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	testModelDeploymentName = "test-model-deployment-name"
)

type JwtSuite struct {
	suite.Suite
	g      *GomegaWithT
	server *gin.Engine
}

func (s *JwtSuite) SetupSuite() {
	s.server = gin.Default()
	v1Group := s.server.Group("")
	dep_route.ConfigureRoutes(v1Group, nil)
}

func (s *JwtSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestJwtSuite(t *testing.T) {
	suite.Run(t, new(JwtSuite))
}

func (s *JwtSuite) TestGenerateTokenWithoutExpirationDate() {
	privateKey, err := ioutil.ReadFile("../../../../../hack/tests/keys/private_key.pem")
	s.g.Expect(err).ShouldNot(HaveOccurred())
	viper.Set(md_config.SecurityJwtPrivateKey, base64.StdEncoding.EncodeToString(privateKey))

	viper.Set(md_config.SecurityJwtEnabled, true)

	tokenRequest := &deployment.TokenRequest{RoleName: testModelDeploymentName}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelJwtUrl, bytes.NewReader(tokenRequestBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	s.g.Expect(w.Code).To(Equal(http.StatusCreated))

	var result deployment.TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(result.Token).ToNot(BeEmpty())
}

func (s *JwtSuite) TestDisabledJWT() {
	viper.Set(md_config.SecurityJwtEnabled, false)

	tokenRequest := &deployment.TokenRequest{RoleName: testModelDeploymentName}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, dep_route.CreateModelJwtUrl, bytes.NewReader(tokenRequestBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	s.g.Expect(w.Code).To(Equal(http.StatusCreated))

	var result deployment.TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(result.Token).To(BeEmpty())
}
