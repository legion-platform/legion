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

package packaging

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logPi = logf.Log.WithName("toolchain-integration-controller")

const (
	getPackagingIntegrationURL    = "/packaging/integration/:id"
	getAllPackagingIntegrationURL = "/packaging/integration"
	createPackagingIntegrationURL = "/packaging/integration"
	updatePackagingIntegrationURL = "/packaging/integration"
	deletePackagingIntegrationURL = "/packaging/integration/:id"
	IDPiURLParam                  = "id"
)

var (
	emptyCache = map[string]int{}
)

type PackagingIntegrationController struct {
	repository mp_repository.Repository
	validator  *PiValidator
}

// @Summary Get a PackagingIntegration
// @Description Get a PackagingIntegration by id
// @Tags Packager
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "PackagingIntegration id"
// @Success 200 {object} packaging.PackagingIntegration
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/packaging/integration/{id} [get]
func (pic *PackagingIntegrationController) getPackagingIntegration(c *gin.Context) {
	piID := c.Param(IDPiURLParam)

	pi, err := pic.repository.GetPackagingIntegration(piID)
	if err != nil {
		logPi.Error(err, fmt.Sprintf("Retrieving %s packaging integration", piID))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, pi)
}

// @Summary Get list of PackagingIntegrations
// @Description Get list of PackagingIntegrations
// @Tags Packager
// @Accept  json
// @Produce  json
// @Param size path int false "Number of entities in a response"
// @Param page path int false "Number of a page"
// @Success 200 {array} packaging.PackagingIntegration
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/packaging/integration [get]
func (pic *PackagingIntegrationController) getAllPackagingIntegrations(c *gin.Context) {
	size, page, err := routes.URLParamsToFilter(c, nil, emptyCache)
	if err != nil {
		logPi.Error(err, "Malformed url parameters of packaging integration request")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	piList, err := pic.repository.GetPackagingIntegrationList(
		kubernetes.Size(size),
		kubernetes.Page(page),
	)
	if err != nil {
		logPi.Error(err, "Retrieving list of packaging integrations")
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, piList)
}

// @Summary Create a PackagingIntegration
// @Description Create a PackagingIntegration. Results is created PackagingIntegration.
// @Param ti body packaging.PackagingIntegration true "Create a PackagingIntegration"
// @Tags Packager
// @Accept  json
// @Produce  json
// @Success 201 {object} packaging.PackagingIntegration
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/packaging/integration [post]
func (pic *PackagingIntegrationController) createPackagingIntegration(c *gin.Context) {
	var pi packaging.PackagingIntegration

	if err := c.ShouldBindJSON(&pi); err != nil {
		logPi.Error(err, "JSON binding of the packaging integration is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := pic.validator.ValidateAndSetDefaults(&pi); err != nil {
		logPi.Error(err, fmt.Sprintf("Validation of the packaging integration is failed: %v", pi))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := pic.repository.CreatePackagingIntegration(&pi); err != nil {
		logPi.Error(err, fmt.Sprintf("Creation of the packaging integration: %+v", pi))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusCreated, pi)
}

// @Summary Update a PackagingIntegration
// @Description Update a PackagingIntegration. Results is updated PackagingIntegration.
// @Param pi body packaging.PackagingIntegration true "Update a PackagingIntegration"
// @Tags Packager
// @Accept  json
// @Produce  json
// @Success 200 {object} packaging.PackagingIntegration
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/packaging/integration [put]
func (pic *PackagingIntegrationController) updatePackagingIntegration(c *gin.Context) {
	var pi packaging.PackagingIntegration

	if err := c.ShouldBindJSON(&pi); err != nil {
		logPi.Error(err, "JSON binding of the packaging integration is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := pic.validator.ValidateAndSetDefaults(&pi); err != nil {
		logPi.Error(err, fmt.Sprintf("Validation of the packaging integration is failed: %v", pi))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := pic.repository.UpdatePackagingIntegration(&pi); err != nil {
		logPi.Error(err, fmt.Sprintf("Update of the packaging integration: %+v", pi))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, pi)
}

// @Summary Delete a PackagingIntegration
// @Description Delete a PackagingIntegration by id
// @Tags Packager
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "PackagingIntegration id"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/packaging/integration/{id} [delete]
func (pic *PackagingIntegrationController) deletePackagingIntegration(c *gin.Context) {
	piID := c.Param(IDPiURLParam)

	if err := pic.repository.DeletePackagingIntegration(piID); err != nil {
		logPi.Error(err, fmt.Sprintf("Deletion of %s packaging integration is failed", piID))
		c.AbortWithStatusJSON(routes.CalculateHTTPStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, routes.HTTPResult{Message: fmt.Sprintf("Packaging integration %s was deleted", piID)})
}
