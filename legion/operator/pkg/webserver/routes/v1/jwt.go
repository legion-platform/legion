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

package v1

import (
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"github.com/spf13/viper"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logToken = logf.Log.WithName("log-token")

const (
	createModelJwt = "/model/token"
	getJwks        = "/model/jwks"
)

type TokenRequest struct {
	// Model Deployment name
	RoleName string `json:"role_name"`
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
// @Param token body v1.TokenRequest true "Create a model JWT token"
// @Accept  json
// @Produce  json
// @Success 201 {object} v1.TokenResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/token [post]
func generateToken(c *gin.Context) {
	if !viper.GetBool(legion.JwtEnabled) {
		c.JSON(http.StatusCreated, TokenResponse{Token: ""})
		return
	}

	var tokenRequest TokenRequest

	if err := c.ShouldBindJSON(&tokenRequest); err != nil {
		logToken.Error(err, "Token request")
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	if tokenRequest.RoleName == "" {
		tokenRequest.RoleName = viper.GetString(legion.DefaultRoleName)
	}

	unixExpirationDate, err := utils.CalculateExpirationDate(tokenRequest.ExpirationDate)
	if err != nil {
		logToken.Error(err, "Expiration date calculation")
		routes.AbortWithError(c, 500, err.Error())
	}

	token, err := utils.GenerateModelToken(
		tokenRequest.RoleName, unixExpirationDate,
	)
	if err != nil {
		logToken.Error(err, "Token generation")
		routes.AbortWithError(c, 500, err.Error())
	}

	c.JSON(http.StatusCreated, TokenResponse{Token: token})
}

// @Summary Retrieve model jwks
// @Description Retrieve model jwks for model services
// @Tags JWT
// @Produce  json
// @Success 200 {object} v1.Jwks
// @Router /api/v1/model/jwks [get]
func jwks(c *gin.Context) {
	var jwks Jwks

	if !viper.GetBool(legion.JwtEnabled) {
		c.JSON(http.StatusOK, jwks)
		return
	}

	if err := json.Unmarshal([]byte(utils.Jwks()), &jwks); err != nil {
		routes.AbortWithError(c, 500, "Can not generate jwks")
		return
	}

	c.JSON(http.StatusOK, jwks)
}
