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
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packaging_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	http_util "github.com/legion-platform/legion/legion/operator/pkg/repository/util/http"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	v1Routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1"
	mp_routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	"io/ioutil"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
)

var log = logf.Log.WithName("model_packaging_http_repository")

type httpPackagingRepository struct {
	http_util.BaseEdiClient
}

// todo: doc
func NewRepository(ediURL string, token string) packaging_repository.Repository {
	return &httpPackagingRepository{
		BaseEdiClient: http_util.NewBaseEdiClient(
			ediURL,
			token,
			v1Routes.LegionV1ApiVersion,
		),
	}
}

func wrapMpLogger(id string) logr.Logger {
	return log.WithValues("mp_id", id)
}

func (htr *httpPackagingRepository) GetModelPackaging(id string) (mp *packaging.ModelPackaging, err error) {
	mpLogger := wrapMpLogger(id)

	response, err := htr.DoRequest(
		http.MethodGet,
		strings.Replace(mp_routes.GetModelPackagingURL, ":id", id, 1),
		nil,
	)
	if err != nil {
		mpLogger.Error(err, "Retrieving of the model packaging from EDI failed")

		return nil, err
	}

	mp = &packaging.ModelPackaging{}
	mpBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		mpLogger.Error(err, "Read all data from EDI response")

		return nil, err
	}
	defer func() {
		bodyCloseError := response.Body.Close()
		if bodyCloseError != nil {
			mpLogger.Error(err, "Closing model packaging response body")
		}
	}()

	if response.StatusCode >= 400 {
		return nil, fmt.Errorf("error occures: %s", string(mpBytes))
	}

	err = json.Unmarshal(mpBytes, mp)
	if err != nil {
		mpLogger.Error(err, "Unmarshal the model packaging")

		return nil, err
	}

	return mp, nil
}

func (htr *httpPackagingRepository) GetModelPackagingList(options ...kubernetes.ListOption) (
	[]packaging.ModelPackaging, error,
) {
	panic("not implemented")
}

func (htr *httpPackagingRepository) DeleteModelPackaging(id string) error {
	panic("not implemented")
}

func (htr *httpPackagingRepository) UpdateModelPackaging(mp *packaging.ModelPackaging) error {
	panic("not implemented")

}

func (htr *httpPackagingRepository) CreateModelPackaging(mp *packaging.ModelPackaging) error {
	panic("not implemented")
}

func (htr *httpPackagingRepository) GetModelPackagingLogs(
	id string, writer packaging_repository.Writer, follow bool,
) error {
	panic("not implemented")
}

func (htr *httpPackagingRepository) SaveModelPackagingResult(
	id string,
	result []legionv1alpha1.ModelPackagingResult,
) error {
	mpLogger := wrapMpLogger(id)

	response, err := htr.DoRequest(
		http.MethodPut,
		strings.Replace(mp_routes.SaveModelPackagingResultURL, ":id", id, 1),
		result,
	)
	if err != nil {
		mpLogger.Error(err, "Saving of the model packaging result in EDI failed")

		return err
	}

	if response.StatusCode >= 400 {
		mpBytes, err := ioutil.ReadAll(response.Body)
		if err != nil {
			mpLogger.Error(err, "Read all data from EDI response")

			return err
		}
		defer func() {
			bodyCloseError := response.Body.Close()
			if bodyCloseError != nil {
				mpLogger.Error(err, "Closing model packaging response body")
			}
			if err != nil {
				err = bodyCloseError
			}
		}()

		return fmt.Errorf("error occures: %s", string(mpBytes))
	}

	return nil
}

func (htr *httpPackagingRepository) GetModelPackagingResult(id string) ([]legionv1alpha1.ModelPackagingResult, error) {
	panic("not implemented")
}
