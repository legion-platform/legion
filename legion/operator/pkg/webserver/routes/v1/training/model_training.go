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
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	mt_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"net/http"
	"reflect"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strconv"
)

var logMT = logf.Log.WithName("training-controller")

const (
	GetModelTrainingUrl     = "/model/training/:id"
	GetAllModelTrainingUrl  = "/model/training"
	GetModelTrainingLogsUrl = "/model/training/:id/log"
	CreateModelTrainingUrl  = "/model/training"
	UpdateModelTrainingUrl  = "/model/training"
	DeleteModelTrainingUrl  = "/model/training/:id"
	IdMtUrlParam            = "id"
	FollowUrlParam          = "follow"
)

var (
	fieldsCache = map[string]int{}
)

func init() {
	elem := reflect.TypeOf(&mt_storage.MTFilter{}).Elem()
	for i := 0; i < elem.NumField(); i++ {
		tagName := elem.Field(i).Tag.Get(mt_storage.TagKey)

		fieldsCache[tagName] = i
	}
}

type ModelTrainingController struct {
	mtStorage mt_storage.Storage
	validator *MtValidator
}

// @Summary Get a Model Training
// @Description Get a Model Training by id
// @Tags Training
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model Training id"
// @Success 200 {object} training.ModelTraining
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/training/{id} [get]
func (mtc *ModelTrainingController) getMT(c *gin.Context) {
	mtId := c.Param(IdMtUrlParam)

	mt, err := mtc.mtStorage.GetModelTraining(mtId)
	if err != nil {
		logMT.Error(err, fmt.Sprintf("Retrieving of %s model training", mtId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mt)
}

// @Summary Get list of Model Trainings
// @Description Get list of Model Trainings
// @Tags Training
// @Accept  json
// @Produce  json
// @Param size path int false "Number of entities in a response"
// @Param page path int false "Number of a page"
// @Param model_name path int false "Model name"
// @Param model_version path int false "Model version"
// @Param toolchain path int false "Toolchain name"
// @Success 200 {array} training.ModelTraining
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/training [get]
func (mtc *ModelTrainingController) getAllMTs(c *gin.Context) {
	filter := &mt_storage.MTFilter{}
	size, page, err := routes.UrlParamsToFilter(c, filter, fieldsCache)
	if err != nil {
		logMT.Error(err, "Malformed url parameters of model training request")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	mtList, err := mtc.mtStorage.GetModelTrainingList(
		kubernetes.ListFilter(filter),
		kubernetes.Size(size),
		kubernetes.Page(page),
	)
	if err != nil {
		logMT.Error(err, "Retrieving list of model trainings")
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, &mtList)
}

// @Summary Create a Model Training
// @Description Create a Model Training. Results is created Model Training.
// @Param mt body training.ModelTraining true "Create a Model Training"
// @Tags Training
// @Accept  json
// @Produce  json
// @Success 201 {object} training.ModelTraining
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/training [post]
func (mtc *ModelTrainingController) createMT(c *gin.Context) {
	var mt training.ModelTraining

	if err := c.ShouldBindJSON(&mt); err != nil {
		logMT.Error(err, "JSON binding of the model training is failed")
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mtc.validator.ValidatesAndSetDefaults(&mt); err != nil {
		logMT.Error(err, fmt.Sprintf("Validation of the model training is failed: %v", mt))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mtc.mtStorage.CreateModelTraining(&mt); err != nil {
		logMT.Error(err, fmt.Sprintf("Creation of the model training: %v", mt))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusCreated, mt)
}

// @Summary Update a Model Training
// @Description Update a Model Training. Results is updated Model Training.
// @Param mt body training.ModelTraining true "Update a Model Training"
// @Tags Training
// @Accept  json
// @Produce  json
// @Success 200 {object} training.ModelTraining
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/training [put]
func (mtc *ModelTrainingController) updateMT(c *gin.Context) {
	var mt training.ModelTraining

	if err := c.ShouldBindJSON(&mt); err != nil {
		logMT.Error(err, fmt.Sprintf("JSON binding of the model training is failed: %v", mt))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mtc.validator.ValidatesAndSetDefaults(&mt); err != nil {
		logMT.Error(err, fmt.Sprintf("Creation of the model training: %v", mt))
		c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: err.Error()})

		return
	}

	if err := mtc.mtStorage.UpdateModelTraining(&mt); err != nil {
		logMT.Error(err, fmt.Sprintf("Creation of the model training: %v", mt))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, mt)
}

// @Summary Get a Model Training
// @Description Get a Model Training by id
// @Tags Training
// @Name id
// @Accept  json
// @Produce  json
// @Param id path string true "Model Training id"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 400 {object} routes.HTTPResult
// @Router /api/v1/model/training/{id} [delete]
func (mtc *ModelTrainingController) deleteMT(c *gin.Context) {
	mtId := c.Param(IdMtUrlParam)

	if err := mtc.mtStorage.DeleteModelTraining(mtId); err != nil {
		logMT.Error(err, fmt.Sprintf("Deletion of %s model training is failed", mtId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}

	c.JSON(http.StatusOK, routes.HTTPResult{Message: fmt.Sprintf("Model training %s was deleted", mtId)})
}

// @Summary Stream logs from model training pod
// @Description Stream logs from model training pod
// @Tags Training
// @Name id
// @Produce  plain
// @Accept  plain
// @Param follow query bool false "follow logs"
// @Param id path string true "Model Training id"
// @Success 200 {string} string
// @Failure 400 {string} string
// @Router /api/v1/model/training/{id}/log [get]
func (mtc *ModelTrainingController) getModelTrainingLog(c *gin.Context) {
	mtId := c.Param(IdMtUrlParam)
	follow := false
	var err error

	urlParameters := c.Request.URL.Query()
	followParam := urlParameters.Get(FollowUrlParam)

	if len(followParam) != 0 {
		follow, err = strconv.ParseBool(followParam)
		if err != nil {
			errMessage := fmt.Sprintf("Convert %s to bool", followParam)
			logMT.Error(err, errMessage)
			c.AbortWithStatusJSON(http.StatusBadRequest, routes.HTTPResult{Message: errMessage})

			return
		}
	}

	if err := mtc.mtStorage.GetModelTrainingLogs(mtId, c.Writer, follow); err != nil {
		logMT.Error(err, fmt.Sprintf("Getting %s model training logs is failed", mtId))
		c.AbortWithStatusJSON(routes.CalculateHttpStatusCode(err), routes.HTTPResult{Message: err.Error()})

		return
	}
}
