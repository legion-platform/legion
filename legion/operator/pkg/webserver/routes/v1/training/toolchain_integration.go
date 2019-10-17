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

package training

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	mt_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logTI = logf.Log.WithName("toolchain-integration-controller")

const (
	GetToolchainIntegrationURL    = "/toolchain/integration/:id"
	GetAllToolchainIntegrationURL = "/toolchain/integration"
	CreateToolchainIntegrationURL = "/toolchain/integration"
	UpdateToolchainIntegrationURL = "/toolchain/integration"
	DeleteToolchainIntegrationURL = "/toolchain/integration/:id"
	IDTiURLParam                  = "id"
)

var (
	emptyCache = map[string]int{}
)

type ToolchainIntegrationController struct {
	repository mt_repository.Repository
	validator  *TiValidator
}

// @Summary Get a ToolchainIntegration
// @Description Get a ToolchainIntegration by id
// @Tags Toolchain
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "ToolchainIntegration id"
// @Success 200 {object} training.ToolchainIntegration
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/toolchain/integration/{id} [get]
func (tic *ToolchainIntegrationController) getToolchainIntegration(c *gin.Context) {
	tiID := c.Param(IDTiURLParam)

	ti, err := tic.repository.GetToolchainIntegration(tiID)
	if err != nil {
		logTI.Error(err, fmt.Sprintf("Retrieving %s toolchain integration", tiID))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, ti)
}

// @Summary Get list of ToolchainIntegrations
// @Description Get list of ToolchainIntegrations
// @Tags Toolchain
// @Accept  json
// @Produce  json
// @Param size path int false "Number of entities in a response"
// @Param page path int false "Number of a page"
// @Success 200 {array} training.ToolchainIntegration
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/toolchain/integration [get]
func (tic *ToolchainIntegrationController) getAllToolchainIntegrations(c *gin.Context) {
	size, page, err := routes.URLParamsToFilter(c, nil, emptyCache)
	if err != nil {
		logTI.Error(err, fmt.Sprintf("Malformed url parameters of toolchain itergration request"))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	tiList, err := tic.repository.GetToolchainIntegrationList(
		kubernetes.Size(size),
		kubernetes.Page(page),
	)
	if err != nil {
		logTI.Error(err, fmt.Sprintf("Retrieving list of toolchain integrations"))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, &tiList)
}

// @Summary Create a ToolchainIntegration
// @Description Create a ToolchainIntegration. Results is created ToolchainIntegration.
// @Param ti body training.ToolchainIntegration true "Create a ToolchainIntegration"
// @Tags Toolchain
// @Accept  json
// @Produce  json
// @Success 201 {object} training.ToolchainIntegration
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/toolchain/integration [post]
func (tic *ToolchainIntegrationController) createToolchainIntegration(c *gin.Context) {
	var ti training.ToolchainIntegration

	if err := c.ShouldBindJSON(&ti); err != nil {
		logTI.Error(err, fmt.Sprintf("JSON binding of toolchain integration is failed"))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := tic.validator.ValidatesAndSetDefaults(&ti); err != nil {
		logMT.Error(err, fmt.Sprintf("Validation of the tollchain integration is failed: %v", ti))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := tic.repository.CreateToolchainIntegration(&ti); err != nil {
		logTI.Error(err, fmt.Sprintf("Creation of toolchain integration: %v", ti))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusCreated, ti)
}

// @Summary Update a ToolchainIntegration
// @Description Update a ToolchainIntegration. Results is updated ToolchainIntegration.
// @Param ti body training.ToolchainIntegration true "Update a ToolchainIntegration"
// @Tags Toolchain
// @Accept  json
// @Produce  json
// @Success 200 {object} training.ToolchainIntegration
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/toolchain/integration [put]
func (tic *ToolchainIntegrationController) updateToolchainIntegration(c *gin.Context) {
	var ti training.ToolchainIntegration

	if err := c.ShouldBindJSON(&ti); err != nil {
		logTI.Error(err, fmt.Sprintf("JSON binding of toolchain integration is failed"))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := tic.validator.ValidatesAndSetDefaults(&ti); err != nil {
		logMT.Error(err, fmt.Sprintf("Validation of the tollchain integration is failed: %v", ti))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := tic.repository.UpdateToolchainIntegration(&ti); err != nil {
		logTI.Error(err, fmt.Sprintf("Update of toolchain integration: %v", ti))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, ti)
}

// @Summary Delete a ToolchainIntegration
// @Description Delete a ToolchainIntegration by id
// @Tags Toolchain
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "ToolchainIntegration id"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/toolchain/integration/{id} [delete]
func (tic *ToolchainIntegrationController) deleteToolchainIntegration(c *gin.Context) {
	tiID := c.Param(IDTiURLParam)

	if err := tic.repository.DeleteToolchainIntegration(tiID); err != nil {
		logTI.Error(err, fmt.Sprintf("Deletion of %s toolchain integration is failed", tiID))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, routes.HTTPResult{Message: fmt.Sprintf("ToolchainIntegration %s was deleted", tiID)})
}
