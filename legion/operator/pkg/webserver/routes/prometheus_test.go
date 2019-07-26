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

package routes_test

import (
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"net/http"
	"net/http/httptest"
	"testing"
)

type PrometheusSuite struct {
	suite.Suite
	g      *GomegaWithT
	server *gin.Engine
}

func (s *PrometheusSuite) SetupSuite() {
	s.server = gin.Default()
	routes.SetUpPrometheus(s.server)
}

func (s *PrometheusSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestSuite(t *testing.T) {
	suite.Run(t, new(PrometheusSuite))
}

func (s *PrometheusSuite) TestMonitoring() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/metrics", nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))

	responseBody := w.Body.String()
	// Gin metrics
	s.g.Expect(responseBody).Should(ContainSubstring("gin_request_duration_seconds"))
	// Golang metrics
	s.g.Expect(responseBody).Should(ContainSubstring("go_memstats_stack_inuse_bytes"))
	// System metrics
	s.g.Expect(responseBody).Should(ContainSubstring("process_open_fds"))
}
