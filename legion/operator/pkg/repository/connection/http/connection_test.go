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

package http_test

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	conn_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/http"
	conn_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/connection"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
)

const (
	connID           = "test-conn-id"
	testDecryptToken = "test-decrypt-token" //nolint
)

type Suite struct {
	suite.Suite
	g              *GomegaWithT
	ts             *httptest.Server
	connHTTPClient conn_repository.Repository
}

func newStubConn() *connection.Connection {
	return &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:     connection.DockerType,
			URI:      "test-uri:/123",
			Username: "test-username",
		},
	}
}

func NotFound(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotFound)
	_, err := fmt.Fprintf(w, "%s url not found", r.URL.Path)
	if err != nil {
		// Must not be occurred
		panic(err)
	}
}

func (s *Suite) SetupSuite() {
	s.ts = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/v1/connection/test-conn-id":
			s.processGetConnection(r, w, newStubConn().DeleteSensitiveData())
		case "/api/v1/connection/test-conn-id/decrypted":
			if testDecryptToken != r.URL.Query().Get(conn_routes.ConnDecryptTokenQueryParam) {
				w.WriteHeader(http.StatusBadRequest)
			} else {
				s.processGetConnection(r, w, newStubConn())
			}
		default:
			NotFound(w, r)
		}
	}))

	s.connHTTPClient = conn_http_repository.NewRepository(s.ts.URL, testDecryptToken)
}

func (s *Suite) processGetConnection(r *http.Request, w http.ResponseWriter, conn *connection.Connection) {
	if r.Method != http.MethodGet {
		NotFound(w, r)
		return
	}

	w.WriteHeader(http.StatusOK)
	connBytes, err := json.Marshal(conn)
	if err != nil {
		// Must not be occurred
		panic(err)
	}
	_, err = w.Write(connBytes)
	if err != nil {
		// Must not be occurred
		panic(err)
	}
}

func (s *Suite) TearDownSuite() {
	s.ts.Close()
}

func (s *Suite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestSuite(t *testing.T) {
	suite.Run(t, new(Suite))
}

func (s *Suite) TestConnectionGet() {
	connResult, err := s.connHTTPClient.GetConnection(connID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(newStubConn().DeleteSensitiveData()).Should(Equal(connResult))
}

func (s *Suite) TestConnectionNotFound() {
	_, err := s.connHTTPClient.GetConnection("conn-not-found")
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}

func (s *Suite) TestDecryptedConnectionGet() {
	connResult, err := s.connHTTPClient.GetDecryptedConnection(connID, testDecryptToken)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(newStubConn()).Should(Equal(connResult))
}

func (s *Suite) TestDecryptedConnectionGetWrongToken() {
	_, err := s.connHTTPClient.GetDecryptedConnection(connID, "wrong-token")
	s.g.Expect(err).Should(HaveOccurred())
}

func (s *Suite) TestDecryptedConnectionGetNotFound() {
	_, err := s.connHTTPClient.GetDecryptedConnection("conn-not-found", testDecryptToken)
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}
