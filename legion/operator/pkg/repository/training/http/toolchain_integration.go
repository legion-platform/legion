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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	train_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/training"
	"io/ioutil"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
)

var logTI = logf.Log.WithName("toolchain_integration_http_repository")

func wrapTiLogger(id string) logr.Logger {
	return logTI.WithValues("ti_id", id)
}

func (htr *httpTrainingRepository) GetToolchainIntegration(id string) (ti *training.ToolchainIntegration, err error) {
	tiLogger := wrapTiLogger(id)

	response, err := htr.DoRequest(
		http.MethodGet,
		strings.Replace(train_routes.GetToolchainIntegrationURL, ":id", id, 1),
		nil,
	)
	if err != nil {
		tiLogger.Error(err, "Retrieving of the toolchain integration from EDI failed")

		return nil, err
	}

	ti = &training.ToolchainIntegration{}
	tiBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		tiLogger.Error(err, "Read all data from EDI response")

		return nil, err
	}
	defer func() {
		bodyCloseError := response.Body.Close()
		if bodyCloseError != nil {
			tiLogger.Error(err, "Closing toolchain integration response body")
		}
	}()

	if response.StatusCode >= 400 {
		return nil, fmt.Errorf("error occures: %s", string(tiBytes))
	}

	err = json.Unmarshal(tiBytes, ti)
	if err != nil {
		tiLogger.Error(err, "Unmarshal the toolchain integration")

		return nil, err
	}

	return ti, nil
}

func (htr *httpTrainingRepository) GetToolchainIntegrationList(options ...kubernetes.ListOption) (
	[]training.ToolchainIntegration, error,
) {
	panic("not implemented")
}

func (htr *httpTrainingRepository) DeleteToolchainIntegration(id string) error {
	panic("not implemented")
}

func (htr *httpTrainingRepository) UpdateToolchainIntegration(ti *training.ToolchainIntegration) error {
	panic("not implemented")

}

func (htr *httpTrainingRepository) CreateToolchainIntegration(ti *training.ToolchainIntegration) error {
	panic("not implemented")

}
