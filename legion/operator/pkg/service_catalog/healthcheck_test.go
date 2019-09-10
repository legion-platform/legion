/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package service_catalog_test

import (
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"net/http"
	"net/http/httptest"
	"testing"
)

type HealthCheckSuite struct {
	suite.Suite
	g      *GomegaWithT
	server *gin.Engine
}

func (s *HealthCheckSuite) SetupSuite() {
	s.server = gin.Default()
	service_catalog.SetUpHealthCheck(s.server)
}

func (s *HealthCheckSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestHealthCheckSuite(t *testing.T) {
	suite.Run(t, new(HealthCheckSuite))
}

func (s *HealthCheckSuite) TestHealthCheck() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, service_catalog.HealthCheckURL, nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var response map[string]string
	err = json.Unmarshal(w.Body.Bytes(), &response)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(response).Should(Equal(make(map[string]string, 0)))
}
