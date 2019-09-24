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

package configuration_test

import (
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/configuration"
	common_conf "github.com/legion-platform/legion/legion/operator/pkg/config/common"
	"github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	conf_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/configuration"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	"github.com/stretchr/testify/suite"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	urlName   = "Training Api"
	urlValue  = "https://training.legion.org"
	metricUrl = "https://metrics.legion.org"
)

type ConfigurationRouteSuite struct {
	suite.Suite
	g      *GomegaWithT
	server *gin.Engine
}

func (s *ConfigurationRouteSuite) SetupSuite() {
	s.server = gin.Default()
	v1Group := s.server.Group("")
	conf_route.ConfigureRoutes(v1Group)
}

func (s *ConfigurationRouteSuite) TearDownTest() {
	viper.Set(common_conf.ExternalUrls, []interface{}{})
}

func (s *ConfigurationRouteSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestConnectionRouteSuite(t *testing.T) {
	suite.Run(t, new(ConfigurationRouteSuite))
}

func (s *ConfigurationRouteSuite) TestGetConfiguration() {
	externalUrls := []interface{}{}
	externalUrls = append(externalUrls, map[interface{}]interface{}{"name": urlName, "url": urlValue})
	viper.Set(common_conf.ExternalUrls, externalUrls)

	viper.Set(training.MetricUrl, metricUrl)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		conf_route.GetConfigurationUrl,
		nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result configuration.Configuration
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(Equal(configuration.Configuration{
		CommonConfiguration: configuration.CommonConfiguration{
			ExternalUrls: []configuration.ExternalUrl{
				{
					Name: urlName,
					URL:  urlValue,
				},
			},
		},
		TrainingConfiguration: configuration.TrainingConfiguration{MetricUrl: metricUrl},
	}))
}

func (s *ConfigurationRouteSuite) TestGetEmptyListOfUrlsConfiguration() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodGet,
		conf_route.GetConfigurationUrl,
		nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result configuration.Configuration
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result.CommonConfiguration.ExternalUrls).Should(HaveLen(0))
}

func (s *ConfigurationRouteSuite) TestUpdateConfiguration() {
	w := httptest.NewRecorder()
	req, err := http.NewRequest(
		http.MethodPut,
		conf_route.UpdateConfigurationUrl,
		nil)
	s.g.Expect(err).NotTo(HaveOccurred())
	s.server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	s.g.Expect(err).NotTo(HaveOccurred())

	s.g.Expect(w.Code).Should(Equal(http.StatusOK))
	s.g.Expect(result).Should(Equal(routes.HTTPResult{Message: "This is stub for now"}))
}
