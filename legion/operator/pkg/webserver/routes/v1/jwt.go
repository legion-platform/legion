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
)

type TokenRequest struct {
	// Model id
	ModelID string `json:"model_id"`
	// Model version
	ModelVersion string `json:"model_version"`
	// Explicitly set expiration date for token
	ExpirationDate string `json:"expiration_date,omitempty"`
}

type TokenResponse struct {
	Token string `json:"token"`
}

// @Summary Create a model JWT token
// @Description Create a JWT token for access to the model service
// @Tags Token
// @Param token body v1.TokenRequest true "Create a model JWT token"
// @Accept  json
// @Produce  json
// @Success 201 {object} v1.TokenResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/token [post]
func generateToken(c *gin.Context) {
	if viper.GetString(legion.JwtSecret) == "" {
		c.JSON(http.StatusCreated, TokenResponse{Token: ""})
		return
	}

	var tokenRequest TokenRequest

	if err := c.ShouldBindJSON(&tokenRequest); err != nil {
		logToken.Error(err, "Token request")
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	if tokenRequest.ModelVersion == "" {
		routes.AbortWithError(c, 500, "Requested field model_version is not set")
		return
	}

	if tokenRequest.ModelID == "" {
		routes.AbortWithError(c, 500, "Requested field model_id is not set")
		return
	}

	unixExpirationDate, err := utils.CalculateExpirationDate(tokenRequest.ExpirationDate)
	if err != nil {
		logToken.Error(err, "Expiration date calculation")
		routes.AbortWithError(c, 500, err.Error())
	}

	token, err := utils.GenerateModelToken(
		tokenRequest.ModelID, tokenRequest.ModelVersion, unixExpirationDate,
	)
	if err != nil {
		logToken.Error(err, "Token generation")
		routes.AbortWithError(c, 500, err.Error())
	}

	c.JSON(http.StatusCreated, TokenResponse{Token: token})
}
