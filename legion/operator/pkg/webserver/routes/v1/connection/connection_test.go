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

package connection_test

import (
	"bytes"
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	conn_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	conn_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/connection"
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
	connId        = "testconn"
	connId1       = "testconn1"
	connId2       = "testconn2"
	connReference = "refs/heads/master"
	connURI       = "git@github.com:legion-platform/legion.git"
	creds         = "bG9sCg=="
)

type ConnectionRouteSuite struct {
	suite.Suite
	g           *GomegaWithT
	server      *gin.Engine
	connStorage conn_storage.Storage
}

func (s *ConnectionRouteSuite) SetupSuite() {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	s.server = gin.Default()
	v1Group := s.server.Group("")
	s.connStorage = conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient())
	conn_route.ConfigureRoutes(v1Group, s.connStorage)
}

func (s *ConnectionRouteSuite) TearDownTest() {
	for _, connId := range []string{connId, connId1, connId2} {
		if err := s.connStorage.DeleteConnection(connId); err != nil && !errors.IsNotFound(err) {
			// If a connection is not found then it was not created during a test case
			// All other errors propagate as a panic
			panic(err)
		}
	}
}

func (s *ConnectionRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func (s *ConnectionRouteSuite) newMultipleConnStubs() []*connection.Connection {
	conn1 := newConnStub()
	conn1.Id = connId1
	s.g.Expect(s.connStorage.CreateConnection(conn1)).NotTo(HaveOccurred())

	conn2 := newConnStub()
	conn2.Id = connId2
	s.g.Expect(s.connStorage.CreateConnection(conn2)).NotTo(HaveOccurred())

	return []*connection.Connection{conn1, conn2}
}

func TestConnectionRouteSuite(t *testing.T) {
	suite.Run(t, new(ConnectionRouteSuite))
}

func newConnStub() *connection.Connection {
	return &connection.Connection{
		Id: connId,
		Spec: v1alpha1.ConnectionSpec{
			Type:     connection.DockerType,
			URI:      connURI,
			Username: "username",
			Password: "password",
		},
	}
}

func (s *ConnectionRouteSuite) TestGetConnection() {
	conn := newConnStub()
	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(conn_route.GetConnectionUrl, ":id", connId, -1),
		nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(Equal(connection.Connection{Id: conn.Id, Spec: conn.Spec, Status: &v1alpha1.ConnectionStatus{}}))
}

func (s *ConnectionRouteSuite) TestGetConnectionNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		strings.Replace(conn_route.GetConnectionUrl, ":id", "not-found", -1),
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

func (s *ConnectionRouteSuite) TestGetAllConnections() {
	conn := newConnStub()
	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		conn_route.GetAllConnectionUrl,
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	s.g.Expect(result[0].Id).Should(Equal(conn.Id))
	s.g.Expect(result[0].Spec).Should(Equal(conn.Spec))
}

func (s *ConnectionRouteSuite) TestGetAllEmptyConnections() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		conn_route.GetAllConnectionUrl,
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(0))
}

func (s *ConnectionRouteSuite) TestGetAllConnectionsByType() {
	connGit := &connection.Connection{
		Id: connId1,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	s.g.Expect(s.connStorage.CreateConnection(connGit)).NotTo(HaveOccurred())

	connDocker := &connection.Connection{
		Id: connId2,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.DockerType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	s.g.Expect(s.connStorage.CreateConnection(connDocker)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, conn_route.GetAllConnectionUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("type", string(connection.GITType))
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	s.g.Expect(result[0].Id).Should(Equal(connGit.Id))
	s.g.Expect(result[0].Spec).Should(Equal(connGit.Spec))
}

func (s *ConnectionRouteSuite) TestGetAllConnectionsMultipleFiltersByType() {
	connGit := &connection.Connection{
		Id: connId1,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	s.g.Expect(s.connStorage.CreateConnection(connGit)).NotTo(HaveOccurred())

	connDocker := &connection.Connection{
		Id: connId2,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.DockerType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	s.g.Expect(s.connStorage.CreateConnection(connDocker)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, conn_route.GetAllConnectionUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("type", string(connection.GITType))
	query.Add("type", string(connection.DockerType))
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(2))
}

func (s *ConnectionRouteSuite) TestGetAllConnectionsPaging() {
	s.newMultipleConnStubs()

	connNames := map[string]interface{}{connId1: nil, connId2: nil}

	// Return first page
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, conn_route.GetAllConnectionUrl, nil)
	s.g.Expect(err).NotTo(HaveOccurred())

	query := req.URL.Query()
	query.Set("size", "1")
	query.Set("page", "0")
	req.URL.RawQuery = query.Encode()

	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result []connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(HaveLen(1))
	delete(connNames, result[0].Id)

	// Return second page
	w = httptest.NewRecorder()
	req, err = http.NewRequest(http.MethodGet, conn_route.GetAllConnectionUrl, nil)
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
	req, err = http.NewRequest(http.MethodGet, conn_route.GetAllConnectionUrl, nil)
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

func (s *ConnectionRouteSuite) TestCreateConnection() {
	connEntity := newConnStub()

	connEntityBody, err := json.Marshal(connEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, conn_route.CreateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var connResponse connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &connResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusCreated))
	s.g.Expect(connResponse.Id).Should(Equal(connEntity.Id))
	s.g.Expect(connResponse.Spec).Should(Equal(connEntity.Spec))

	conn, err := s.connStorage.GetConnection(connId)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(conn.Id).To(Equal(connEntity.Id))
	s.g.Expect(conn.Spec).To(Equal(connEntity.Spec))
}

func (s *ConnectionRouteSuite) TestCreateDuplicateConnection() {
	conn := newConnStub()

	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	connEntityBody, err := json.Marshal(conn)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, conn_route.CreateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusConflict))
	s.g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func (s *ConnectionRouteSuite) TestValidateCreateConnection() {
	conn := newConnStub()
	conn.Spec.Type = "not-found-type"

	connEntityBody, err := json.Marshal(conn)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, conn_route.CreateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).Should(ContainSubstring("unknown type: not-found-type"))
}

func (s *ConnectionRouteSuite) TestUpdateConnection() {
	conn := newConnStub()
	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	connEntity := newConnStub()
	connEntity.Spec.URI = "new-uri"

	connEntityBody, err := json.Marshal(connEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, conn_route.UpdateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var connResponse connection.Connection
	err = json.Unmarshal(w.Body.Bytes(), &connResponse)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(connResponse.Id).Should(Equal(connEntity.Id))
	s.g.Expect(connResponse.Spec).Should(Equal(connEntity.Spec))

	conn, err = s.connStorage.GetConnection(connId)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(conn.Spec).To(Equal(connEntity.Spec))
}

func (s *ConnectionRouteSuite) TestUpdateConnectionNotFound() {
	connEntity := newConnStub()

	connEntityBody, err := json.Marshal(connEntity)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, conn_route.UpdateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	s.g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func (s *ConnectionRouteSuite) TestValidateUpdateConnection() {
	conn := newConnStub()
	conn.Spec.Type = "not-found-type"
	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	connEntityBody, err := json.Marshal(conn)
	s.g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, conn_route.CreateConnectionUrl, bytes.NewReader(connEntityBody))
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusBadRequest))
	s.g.Expect(result.Message).Should(ContainSubstring("unknown type: not-found-type"))
}

func (s *ConnectionRouteSuite) TestDeleteConnection() {
	conn := newConnStub()
	s.g.Expect(s.connStorage.CreateConnection(conn)).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(conn_route.DeleteConnectionUrl, ":id", connId, -1),
		nil,
	)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	connList, err := s.connStorage.GetConnectionList()
	s.g.Expect(err).NotTo(HaveOccurred())
	s.g.Expect(connList).To(HaveLen(0))
}

func (s *ConnectionRouteSuite) TestDeleteConnectionNotFound() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodDelete,
		strings.Replace(conn_route.DeleteConnectionUrl, ":id", "not-found", -1),
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
