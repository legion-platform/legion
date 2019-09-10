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
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	mr_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"

	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logMR = logf.Log.WithName("mr-controller")

const (
	GetModelRouteUrl    = "/model/route/:id"
	GetAllModelRouteUrl = "/model/route"
	CreateModelRouteUrl = "/model/route"
	UpdateModelRouteUrl = "/model/route"
	DeleteModelRouteUrl = "/model/route/:id"
	IdMrUrlParam        = "id"
)

var (
	emptyCache = map[string]int{}
)

type ModelRouteController struct {
	mrStorage mr_storage.Storage
	validator *MrValidator
}

// @Summary Get a Model route
// @Description Get a Model route by id
// @Tags Route
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model route id"
// @Success 200 {object} deployment.ModelRoute
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/route/{id} [get]
func (mrc *ModelRouteController) getMR(c *gin.Context) {
	mrId := c.Param(IdMrUrlParam)

	mr, err := mrc.mrStorage.GetModelRoute(mrId)
	if err != nil {
		logMR.Error(err, fmt.Sprintf("Retrieving %s model route", mrId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mr)
}

// @Summary Get list of Model routes
// @Description Get list of Model routes
// @Tags Route
// @Accept  json
// @Produce  json
// @Param size path int false "Number of entities in a response"
// @Param page path int false "Number of a page"
// @Success 200 {array} deployment.ModelRoute
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/route [get]
func (mrc *ModelRouteController) getAllMRs(c *gin.Context) {
	size, page, err := routes.UrlParamsToFilter(c, nil, emptyCache)
	if err != nil {
		logMR.Error(err, "Malformed url parameters of model route request")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	mrList, err := mrc.mrStorage.GetModelRouteList(
		kubernetes.Size(size),
		kubernetes.Page(page),
	)
	if err != nil {
		logMR.Error(err, "Retrieving list of model routes")
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mrList)
}

// @Summary Create a Model route
// @Description Create a Model route. Results is created Model route.
// @Param mr body deployment.ModelRoute true "Create a Model route"
// @Tags Route
// @Accept  json
// @Produce  json
// @Success 201 {object} deployment.ModelRoute
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/route [post]
func (mrc *ModelRouteController) createMR(c *gin.Context) {
	var mr deployment.ModelRoute

	if err := c.ShouldBindJSON(&mr); err != nil {
		logMR.Error(err, "JSON binding of the model route is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mrc.validator.ValidatesAndSetDefaults(&mr); err != nil {
		logMR.Error(err, fmt.Sprintf("Validation of the model route is failed: %v", mr))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mrc.mrStorage.CreateModelRoute(&mr); err != nil {
		logMR.Error(err, fmt.Sprintf("Creation of the model route: %+v", mr))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusCreated, mr)
}

// @Summary Update a Model route
// @Description Update a Model route. Results is updated Model route.
// @Param mr body deployment.ModelRoute true "Update a Model route"
// @Tags Route
// @Accept  json
// @Produce  json
// @Success 200 {object} deployment.ModelRoute
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/route [put]
func (mrc *ModelRouteController) updateMR(c *gin.Context) {
	var mr deployment.ModelRoute

	if err := c.ShouldBindJSON(&mr); err != nil {
		logMR.Error(err, "JSON binding of the model route is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mrc.validator.ValidatesAndSetDefaults(&mr); err != nil {
		logMR.Error(err, fmt.Sprintf("Validation of the model route is failed: %v", mr))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mrc.mrStorage.UpdateModelRoute(&mr); err != nil {
		logMR.Error(err, fmt.Sprintf("Update of the model route: %+v", mr))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mr)
}

// @Summary Delete a Model route
// @Description Delete a Model route by id
// @Tags Route
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model route id"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/route/{id} [delete]
func (mrc *ModelRouteController) deleteMR(c *gin.Context) {
	mrId := c.Param(IdMrUrlParam)

	if err := mrc.mrStorage.DeleteModelRoute(mrId); err != nil {
		logMR.Error(err, fmt.Sprintf("Deletion of %s model route is failed", mrId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, routes.HTTPResult{Message: fmt.Sprintf("Model route %s was deleted", mrId)})
}
