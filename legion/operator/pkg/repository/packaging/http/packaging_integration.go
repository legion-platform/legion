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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	packaging_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	"io/ioutil"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
)

var logTI = logf.Log.WithName("packaging_integration_http_repository")

func wrapPiLogger(id string) logr.Logger {
	return logTI.WithValues("pi_id", id)
}

func (htr *httpPackagingRepository) GetPackagingIntegration(id string) (pi *packaging.PackagingIntegration, err error) {
	piLogger := wrapPiLogger(id)

	response, err := htr.DoRequest(
		http.MethodGet,
		strings.Replace(packaging_routes.GetPackagingIntegrationURL, ":id", id, 1),
		nil,
	)
	if err != nil {
		piLogger.Error(err, "Retrieving of the packaging integration from EDI failed")

		return nil, err
	}

	pi = &packaging.PackagingIntegration{}
	piBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		piLogger.Error(err, "Read all data from EDI response")

		return nil, err
	}
	defer func() {
		bodyCloseError := response.Body.Close()
		if bodyCloseError != nil {
			piLogger.Error(err, "Closing packaging integration response body")
		}
	}()

	if response.StatusCode >= 400 {
		return nil, fmt.Errorf("error occures: %s", string(piBytes))
	}

	err = json.Unmarshal(piBytes, pi)
	if err != nil {
		piLogger.Error(err, "Unmarshal the packaging integration")

		return nil, err
	}

	return pi, nil
}

func (htr *httpPackagingRepository) GetPackagingIntegrationList(options ...kubernetes.ListOption) (
	[]packaging.PackagingIntegration, error,
) {
	panic("not implemented")
}

func (htr *httpPackagingRepository) DeletePackagingIntegration(id string) error {
	panic("not implemented")
}

func (htr *httpPackagingRepository) UpdatePackagingIntegration(ti *packaging.PackagingIntegration) error {
	panic("not implemented")

}

func (htr *httpPackagingRepository) CreatePackagingIntegration(ti *packaging.PackagingIntegration) error {
	panic("not implemented")

}
