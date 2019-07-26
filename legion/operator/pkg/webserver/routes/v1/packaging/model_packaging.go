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
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"net/http"
	"reflect"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strconv"
)

var logMP = logf.Log.WithName("MP-controller")

const (
	GetModelPackagingUrl     = "/model/packaging/:id"
	GetModelPackagingLogsUrl = "/model/packaging/:id/log"
	GetAllModelPackagingUrl  = "/model/packaging"
	CreateModelPackagingUrl  = "/model/packaging"
	UpdateModelPackagingUrl  = "/model/packaging"
	DeleteModelPackagingUrl  = "/model/packaging/:id"
	IdMpUrlParam             = "id"
	FollowUrlParam           = "follow"
)

var (
	fieldsCache = map[string]int{}
)

func init() {
	elem := reflect.TypeOf(&mp_storage.MPFilter{}).Elem()
	for i := 0; i < elem.NumField(); i++ {
		tagName := elem.Field(i).Tag.Get(mp_storage.TagKey)

		fieldsCache[tagName] = i
	}
}

type ModelPackagingController struct {
	storage   mp_storage.Storage
	validator *MpValidator
}

// @Summary Get a Model Packaging
// @Description Get a Model Packaging by id
// @Tags Packaging
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model Packaging id"
// @Success 200 {object} packaging.ModelPackaging
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/packaging/{id} [get]
func (mpc *ModelPackagingController) getMP(c *gin.Context) {
	mpId := c.Param(IdMpUrlParam)

	mp, err := mpc.storage.GetModelPackaging(mpId)
	if err != nil {
		logMP.Error(err, fmt.Sprintf("Retrieving %s model packaging", mpId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mp)
}

// @Summary Get list of Model Packagings
// @Description Get list of Model Packagings
// @Tags Packaging
// @Accept  json
// @Produce  json
// @Param size path int false "Number of entities in a response"
// @Param page path int false "Number of a page"
// @Success 200 {array} packaging.ModelPackaging
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/packaging [get]
func (mpc *ModelPackagingController) getAllMPs(c *gin.Context) {
	filter := &mp_storage.MPFilter{}
	size, page, err := routes.UrlParamsToFilter(c, filter, fieldsCache)
	if err != nil {
		logMP.Error(err, "Malformed url parameters of model packaging request")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	mpList, err := mpc.storage.GetModelPackagingList(
		kubernetes.ListFilter(filter),
		kubernetes.Size(size),
		kubernetes.Page(page),
	)
	if err != nil {
		logMP.Error(err, "Retrieving list of model packagings")
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mpList)
}

// @Summary Create a Model Packaging
// @Description Create a Model Packaging. Results is created Model Packaging.
// @Param MP body packaging.ModelPackaging true "Create a Model Packaging"
// @Tags Packaging
// @Accept  json
// @Produce  json
// @Success 201 {object} packaging.ModelPackaging
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/packaging [post]
func (mpc *ModelPackagingController) createMP(c *gin.Context) {
	var mp packaging.ModelPackaging

	if err := c.ShouldBindJSON(&mp); err != nil {
		logMP.Error(err, "JSON binding of the model packaging is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mpc.validator.ValidateAndSetDefaults(&mp); err != nil {
		logMP.Error(err, fmt.Sprintf("Validation of the model packaging is failed: %v", mp))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mpc.storage.CreateModelPackaging(&mp); err != nil {
		logMP.Error(err, fmt.Sprintf("Creation of the model packaging: %+v", mp))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusCreated, mp)
}

// @Summary Update a Model Packaging
// @Description Update a Model Packaging. Results is updated Model Packaging.
// @Param MP body packaging.ModelPackaging true "Update a Model Packaging"
// @Tags Packaging
// @Accept  json
// @Produce  json
// @Success 200 {object} packaging.ModelPackaging
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/packaging [put]
func (mpc *ModelPackagingController) updateMP(c *gin.Context) {
	var mp packaging.ModelPackaging

	if err := c.ShouldBindJSON(&mp); err != nil {
		logMP.Error(err, "JSON binding of the model packaging is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mpc.validator.ValidateAndSetDefaults(&mp); err != nil {
		logMP.Error(err, fmt.Sprintf("Validation of the model packaging is failed: %v", mp))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mpc.storage.UpdateModelPackaging(&mp); err != nil {
		logMP.Error(err, fmt.Sprintf("Update of the model packaging: %+v", mp))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mp)
}

// @Summary Delete a Model Packaging
// @Description Delete a Model Packaging by id
// @Tags Packaging
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model Packaging id"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/packaging/{id} [delete]
func (mpc *ModelPackagingController) deleteMP(c *gin.Context) {
	mpId := c.Param(IdMpUrlParam)

	if err := mpc.storage.DeleteModelPackaging(mpId); err != nil {
		logMP.Error(err, fmt.Sprintf("Deletion of %s model packaging is failed", mpId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, routes.HTTPResult{Message: fmt.Sprintf("Model packaging %s was deleted", mpId)})
}

// @Summary Stream logs from model packaging pod
// @Description Stream logs from model packaging pod
// @Tags Packaging
// @Name id
// @Produce  plain
// @Accept  plain
// @Param follow query bool false "follow logs"
// @Param id path string true "Model Packaging id"
// @Success 200 {string} string
// @Failure 400 {string} string
// @Router /api/v1/model/packaging/{id}/log [get]
func (mpc *ModelPackagingController) getModelPackagingLog(c *gin.Context) {
	mpId := c.Param(IdMpUrlParam)
	follow := false
	var err error

	urlParameters := c.Request.URL.Query()
	followParam := urlParameters.Get(FollowUrlParam)

	if len(followParam) != 0 {
		follow, err = strconv.ParseBool(followParam)
		if err != nil {
			errMessage := fmt.Sprintf("Convert %s to bool", followParam)
			logMP.Error(err, errMessage)
			c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: errMessage})

			return
		}
	}

	if err := mpc.storage.GetModelPackagingLogs(mpId, c.Writer, follow); err != nil {
		logMP.Error(err, fmt.Sprintf("Getting %s model packaging logs is failed", mpId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}
}
