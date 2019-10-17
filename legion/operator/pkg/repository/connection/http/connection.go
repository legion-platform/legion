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

package http

import (
	"encoding/json"
	"fmt"
	"github.com/go-logr/logr"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	http_util "github.com/legion-platform/legion/legion/operator/pkg/repository/util/http"
	v1Routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1"
	conn_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/connection"
	"io/ioutil"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
)

var log = logf.Log.WithName("connection-http-repository")

type httpConnectionRepository struct {
	http_util.BaseEdiClient
}

func NewRepository(ediURL string, token string) conn_repository.Repository {
	return &httpConnectionRepository{
		BaseEdiClient: http_util.NewBaseEdiClient(
			ediURL,
			token,
			v1Routes.LegionV1ApiVersion,
		),
	}
}

func wrapConnLogger(id string) logr.Logger {
	return log.WithValues("conn_id", id)
}

func (hcr *httpConnectionRepository) GetConnection(id string) (conn *connection.Connection, err error) {
	connLogger := wrapConnLogger(id)

	response, err := hcr.DoRequest(
		http.MethodGet,
		strings.Replace(conn_routes.GetConnectionURL, ":id", id, 1),
		nil,
	)
	if err != nil {
		connLogger.Error(err, "Retrieving of the connection from EDI failed")

		return nil, err
	}

	conn = &connection.Connection{}
	connBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		connLogger.Error(err, "Read all data from EDI response")

		return nil, err
	}
	defer func() {
		bodyCloseError := response.Body.Close()
		if bodyCloseError != nil {
			connLogger.Error(err, "Closing connection response body")
		}
	}()

	if response.StatusCode >= 400 {
		return nil, fmt.Errorf("error occures: %s", string(connBytes))
	}

	err = json.Unmarshal(connBytes, conn)
	if err != nil {
		connLogger.Error(err, "Unmarshal the connection")

		return nil, err
	}

	return conn, nil
}

func (hcr *httpConnectionRepository) GetConnectionList(options ...conn_repository.ListOption) (
	[]connection.Connection, error,
) {
	panic("not implemented")
}

func (hcr *httpConnectionRepository) DeleteConnection(id string) error {
	panic("not implemented")
}

func (hcr *httpConnectionRepository) UpdateConnection(connection *connection.Connection) error {
	panic("not implemented")

}

func (hcr *httpConnectionRepository) CreateConnection(connection *connection.Connection) error {
	panic("not implemented")

}
