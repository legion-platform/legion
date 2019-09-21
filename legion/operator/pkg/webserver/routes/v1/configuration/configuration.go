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
	GetConfigurationUrl    = "/configuration"
	UpdateConfigurationUrl = "/configuration"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup) {
	routeGroup.GET(GetConfigurationUrl, getConfiguration)
	routeGroup.PUT(UpdateConfigurationUrl, updateConfiguration)
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
	externalUrls := make([]configuration.ExternalUrl, 0)
	configExternalUrls := viper.Get(common_conf.ExternalUrls).([]interface{})
	for _, externalUrlI := range configExternalUrls {
		externalUrl := externalUrlI.(map[interface{}]interface{})

		name := externalUrl["name"].(string)
		url := externalUrl["url"].(string)
		externalUrls = append(externalUrls, configuration.ExternalUrl{
			Name: name,
			URL:  url,
		})
	}

	c.JSON(http.StatusOK, &configuration.Configuration{
		CommonConfiguration: configuration.CommonConfiguration{
			ExternalUrls: externalUrls,
		},
		TrainingConfiguration: configuration.TrainingConfiguration{
			MetricUrl: viper.GetString(training.MetricUrl),
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
