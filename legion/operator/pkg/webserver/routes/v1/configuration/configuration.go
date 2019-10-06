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

package configuration

import (
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/configuration"
	common_conf "github.com/legion-platform/legion/legion/operator/pkg/config/common"
	"github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"github.com/spf13/viper"
	"net/http"
)

const (
	GetConfigurationURL    = "/configuration"
	UpdateConfigurationURL = "/configuration"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup) {
	routeGroup.GET(GetConfigurationURL, getConfiguration)
	routeGroup.PUT(UpdateConfigurationURL, updateConfiguration)
}

// @Summary Get the Legion service configuration
// @Description Get the Legion service configuration
// @Tags Configuration
// @Accept  json
// @Produce  json
// @Success 200 {object} configuration.Configuration
// @Router /api/v1/configuration [get]
func getConfiguration(c *gin.Context) {
	// TODO: move it to a different file
	// TODO: manually mapping is a bad approach
	externalURLs := make([]configuration.ExternalUrl, 0)
	configExternalURLs := viper.Get(common_conf.ExternalURLs).([]interface{})
	for _, externalURL := range configExternalURLs {
		externalURL := externalURL.(map[interface{}]interface{})

		name := externalURL["name"].(string)
		url := externalURL["url"].(string)
		externalURLs = append(externalURLs, configuration.ExternalUrl{
			Name: name,
			URL:  url,
		})
	}

	c.JSON(http.StatusOK, &configuration.Configuration{
		CommonConfiguration: configuration.CommonConfiguration{
			ExternalURLs: externalURLs,
		},
		TrainingConfiguration: configuration.TrainingConfiguration{
			MetricURL: viper.GetString(training.MetricURL),
		},
	})
}

// @Summary Update a Legion service configuration
// @Description Update a Configuration
// @Tags Configuration
// @Param configuration body configuration.Configuration true "Create a Configuration"
// @Accept  json
// @Produce  json
// @Success 200 {object} routes.HTTPResult
// @Router /api/v1/configuration [put]
func updateConfiguration(c *gin.Context) {
	// TODO: find the best way to implement it

	c.JSON(http.StatusOK, routes.HTTPResult{Message: "This is stub for now"})
}
