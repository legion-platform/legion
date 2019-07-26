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

package deployment

import (
	"encoding/json"
	"github.com/gin-gonic/gin"
	dep_config "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"github.com/spf13/viper"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logToken = logf.Log.WithName("log-token")

const (
	CreateModelJwtUrl = "/model/token"
	GetJwksUrl        = "/model/jwks"
)

type TokenRequest struct {
	// Role name
	RoleName string `json:"role_name,omitempty"`
	// Explicitly set expiration date for token
	ExpirationDate string `json:"expiration_date,omitempty"`
}

type TokenResponse struct {
	Token string `json:"token"`
}

type Jwks struct {
	Keys []map[string]string `json:"keys"`
}

// @Summary Create a model JWT token
// @Description Create a JWT token for access to the model service
// @Tags JWT
// @Param token body deployment.TokenRequest true "Create a model JWT token"
// @Accept  json
// @Produce  json
// @Success 201 {object} deployment.TokenResponse
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/token [post]
func generateToken(c *gin.Context) {
	if !viper.GetBool(dep_config.SecurityJwtEnabled) {
		c.JSON(http.StatusCreated, TokenResponse{Token: ""})
		return
	}

	var tokenRequest TokenRequest

	if err := c.ShouldBindJSON(&tokenRequest); err != nil {
		logToken.Error(err, "Token request")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if tokenRequest.RoleName == "" {
		tokenRequest.RoleName = viper.GetString(dep_config.DefaultRoleName)
	}

	unixExpirationDate, err := utils.CalculateExpirationDate(tokenRequest.ExpirationDate)
	if err != nil {
		logToken.Error(err, "Expiration date calculation")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})
	}

	token, err := utils.GenerateModelToken(
		tokenRequest.RoleName, unixExpirationDate,
	)
	if err != nil {
		logToken.Error(err, "Token generation")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})
	}

	c.JSON(http.StatusCreated, TokenResponse{Token: token})
}

// @Summary Retrieve model jwks
// @Description Retrieve model jwks for model services
// @Tags JWT
// @Produce  json
// @Success 200 {object} deployment.TokenResponse
// @Router /api/v1/model/jwks [get]
func jwks(c *gin.Context) {
	var jwks Jwks

	if !viper.GetBool(dep_config.SecurityJwtEnabled) {
		c.JSON(http.StatusOK, jwks)
		return
	}

	if err := json.Unmarshal([]byte(utils.Jwks()), &jwks); err != nil {
		logToken.Error(err, "Can not generate jwks")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, jwks)
}
