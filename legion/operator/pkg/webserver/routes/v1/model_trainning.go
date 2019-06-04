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
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"github.com/spf13/viper"
	"io"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/rest"
	"net/http"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strconv"
)

var logMT = logf.Log.WithName("mt-controller")

const (
	getModelTrainingUrl            = "/model/training/:name"
	getAllModelTrainingUrl         = "/model/training"
	getModelTrainingLogs           = "/model/training/:name/log"
	createModelTrainingUrl         = "/model/training"
	updateModelTrainingUrl         = "/model/training"
	deleteModelTrainingUrl         = "/model/training/:name"
	deleteModelTrainingByLabelsUrl = "/model/training"
)

type ModelTrainingController struct {
	k8sClient client.Client
	k8sConfig *rest.Config
	namespace string
}

type MTRequest struct {
	// MT name
	Name string `json:"name"`
	// MT specification. It is the same as ModelTraining CRD specification
	Spec v1alpha1.ModelTrainingSpec `json:"spec"`
}

type MTResponse struct {
	// MT name
	Name string `json:"name"`
	// MT specification. It is the same as ModelTraining CRD specification
	Spec v1alpha1.ModelTrainingSpec `json:"spec"`
	// MT status. It is the same as ModelTraining CRD status
	Status v1alpha1.ModelTrainingStatus `json:"status,omitempty"`
}

// @Summary Get a Model Training
// @Description Get a Model Training by name
// @Tags ModelTraining
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model Training name"
// @Success 200 {object} v1.MTResponse
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training/{name} [get]
func (controller *ModelTrainingController) getMT(c *gin.Context) {
	mtName := c.Param("name")

	var mt v1alpha1.ModelTraining
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mtName, Namespace: controller.namespace},
		&mt,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Retrieving mt with name %s", mtName))

		return
	}

	c.JSON(http.StatusOK, MTResponse{Name: mtName, Spec: mt.Spec, Status: mt.Status})
}

// @Summary Get list of Model Trainings
// @Description Get list of Model Trainings
// @Tags ModelTraining
// @Accept  json
// @Produce  json
// @Param com.epam.legion.model.id query string false "model id label"
// @Param com.epam.legion.model.version query string false "model version label"
// @Success 200 {array} v1.MTResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training [get]
func (controller *ModelTrainingController) getAllMT(c *gin.Context) {
	// TODO: Maybe we should add filters by labels
	var mtList v1alpha1.ModelTrainingList
	selector, err := mapUrlParamsToLabels(c)
	if err != nil {
		logMD.Error(err, "Malformed url parameters")
		routes.AbortWithError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := controller.k8sClient.List(context.TODO(), &client.ListOptions{
		Namespace: controller.namespace, LabelSelector: selector}, &mtList); err != nil {
		throwK8sError(c, err, "Retrieving list of mt")
		return
	}

	mtEntities := make([]MTResponse, len(mtList.Items))
	for i := 0; i < len(mtList.Items); i++ {
		currentMt := mtList.Items[i]

		mtEntities[i] = MTResponse{Name: currentMt.Name, Spec: currentMt.Spec, Status: currentMt.Status}
	}

	c.JSON(http.StatusOK, &mtEntities)
}

// @Summary Create a Model Training
// @Description Create a Model Training. Result is created Model Training.
// @Param mt body v1.MTRequest true "Create a Model Training"
// @Tags ModelTraining
// @Accept  json
// @Produce  json
// @Success 201 {object} v1.MTResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training [post]
func (controller *ModelTrainingController) createMT(c *gin.Context) {
	var mtEntity MTResponse

	if err := c.ShouldBindJSON(&mtEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	mt := &v1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtEntity.Name,
			Namespace: controller.namespace,
		},
		Spec: mtEntity.Spec,
	}

	if err := controller.k8sClient.Create(context.TODO(), mt); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Creation of the mt: %+v", mt))

		return
	}

	routes.AbortWithSuccess(c, http.StatusCreated, fmt.Sprintf("Model Trainings %+v was created", mtEntity.Name))
}

// @Summary Update a Model Training
// @Description Update a Model Training. Result is updated Model Training.
// @Param mt body v1.MTRequest true "Update a Model Training"
// @Tags ModelTraining
// @Accept  json
// @Produce  json
// @Success 201 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training [put]
func (controller *ModelTrainingController) updateMT(c *gin.Context) {
	var mtEntity MTResponse

	if err := c.ShouldBindJSON(&mtEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	var mt v1alpha1.ModelTraining
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mtEntity.Name, Namespace: controller.namespace},
		&mt,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Update mt with name %s", mtEntity.Name))

		return
	}

	// TODO: think about update, not replacing as for now
	mt.Spec = mtEntity.Spec
	mt.Status.TrainingState = v1alpha1.ModelTrainingUnknown

	if err := controller.k8sClient.Update(context.TODO(), &mt); err != nil {
		logMT.Error(err, fmt.Sprintf("Creation of the mt: %+v", mt))
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model Training %s was updated", mt.Name))
}

// @Summary Get a Model Training
// @Description Get a Model Training by name
// @Tags ModelTraining
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model Training name"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training/{name} [delete]
func (controller *ModelTrainingController) deleteMT(c *gin.Context) {
	mtName := c.Param("name")

	mt := &v1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: controller.namespace,
		},
	}

	if err := controller.k8sClient.Delete(context.TODO(),
		mt,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Dlete mt with name %s", mtName))

		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model Training %s was deleted", mtName))
}

// @Summary Delete list of Model Trainings by labels
// @Description Delete list of  Model Training by labels
// @Tags ModelTraining
// @Name name
// @Accept  json
// @Produce  json
// @Param com.epam.legion.model.id query string false "model id label"
// @Param com.epam.legion.model.version query string false "model version label"
// @Success 200 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/training [delete]
func (controller *ModelTrainingController) deleteMTByLabels(c *gin.Context) {
	var mtList v1alpha1.ModelTrainingList
	selector, err := mapUrlParamsToLabels(c)
	if err != nil {
		logMD.Error(err, "Malformed url parameters")
		routes.AbortWithError(c, http.StatusBadRequest, err.Error())
		return
	}

	if selector.Empty() {
		message := "Selector does not restrict the selection space. Skip deletion."
		logMD.Info(message)
		routes.AbortWithSuccess(c, http.StatusOK, message)

		return
	}

	if err := controller.k8sClient.List(
		context.TODO(), &client.ListOptions{Namespace: controller.namespace, LabelSelector: selector}, &mtList,
	); err != nil {

		throwK8sError(c, err, "Retrieving list of mt")
		return
	}

	if len(mtList.Items) == 0 {
		message := "Not found any model training elements. Skip deletion."
		logMD.Info(message)
		routes.AbortWithSuccess(c, http.StatusOK, message)

		return
	}

	// TODO: Need to parallelize
	for _, mt := range mtList.Items {
		logMD.Info(fmt.Sprintf("Try to delete %s model training", mt.Name))

		if err := controller.k8sClient.Delete(context.TODO(), &mt); err != nil {
			logMD.Error(err, "Model training deletion")
			routes.AbortWithError(c, http.StatusOK, fmt.Sprintf("%s model training deletion is failed", mt.Name))
		} else {
			logMD.Info(fmt.Sprintf("Deletion of %s model training finished successfully", mt.Name))
		}
	}

	routes.AbortWithSuccess(c, http.StatusOK, "Model training were removed")
}

// @Summary Stream logs from model training pod
// @Description Stream logs from model training pod
// @Tags ModelTraining
// @Name name
// @Produce  plain
// @Accept  plain
// @Param follow query bool false "follow logs"
// @Param name path string true "Model Training name"
// @Success 200 {string} string
// @Failure 500 {string} string
// @Router /api/v1/model/training/{name}/log [get]
func (controller *ModelTrainingController) getModelTrainingLog(c *gin.Context) {
	mtName := c.Param("name")
	follow := false
	var err error

	urlParameters := c.Request.URL.Query()
	followParam := urlParameters.Get("follow")

	if len(followParam) != 0 {
		follow, err = strconv.ParseBool(followParam)
		if err != nil {
			errMessage := fmt.Sprintf("Convert %s to bool", followParam)
			logMT.Error(err, errMessage)
			routes.AbortWithError(c, http.StatusBadRequest, errMessage)
			return
		}
	}

	reader, err := utils.StreamTrainingLogs(controller.k8sConfig, mtName, follow)
	if err != nil {
		routes.AbortWithError(c, http.StatusBadRequest, "Creation of log stream")
		return
	}
	defer reader.Close()
	clientGone := c.Writer.CloseNotify()
	for {
		logFlushSize := viper.GetInt64(legion.LogFlushSize)

		select {
		case <-clientGone:
			return
		default:
			_, err := io.CopyN(c.Writer, reader, logFlushSize)
			if err != nil {
				if err != io.EOF {
					logMT.Error(err, "Error during coping of log stream")
				}
				return
			}

			c.Writer.Flush()
		}
	}
}
