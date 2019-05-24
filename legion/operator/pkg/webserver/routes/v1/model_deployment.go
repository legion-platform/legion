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
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"net/http"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logMD = logf.Log.WithName("md-controller")

const (
	getModelDeploymentUrl            = "/model/deployment/:name"
	getAllModelDeploymentUrl         = "/model/deployment"
	createModelDeploymentUrl         = "/model/deployment"
	updateModelDeploymentUrl         = "/model/deployment"
	deleteModelDeploymentUrl         = "/model/deployment/:name"
	deleteModelDeploymentByLabelsUrl = "/model/deployment"
)

type ModelDeploymentController struct {
	k8sClient client.Client
	namespace string
}

type MDRequest struct {
	// Model deployment name
	Name string `json:"name"`
	// Model Deployment specification. It is the same as ModelDeployment CRD specification
	Spec v1alpha1.ModelDeploymentSpec `json:"spec"`
}

type MDResponse struct {
	// Model deployment name
	Name string `json:"name"`
	// Model Deployment specification. It is the same as ModelDeployment CRD specification
	Spec v1alpha1.ModelDeploymentSpec `json:"spec"`
	// Model Deployment specification. It is the same as ModelDeployment CRD specification
	Status *v1alpha1.ModelDeploymentStatus `json:"status,omitempty"`
}

type MDReplicas struct {
	// New number of replicas
	Replicas int32 `json:"replicas"`
}

// @Summary Get a Model deployment
// @Description Get a Model deployment by name
// @Tags ModelDeployment
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model deployment name"
// @Success 200 {object} v1.MDResponse
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment/{name} [get]
func (controller *ModelDeploymentController) getMD(c *gin.Context) {
	mdName := c.Param("name")

	var md v1alpha1.ModelDeployment
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mdName, Namespace: controller.namespace},
		&md,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Retrieving md with name %s", mdName))

		return
	}

	c.JSON(http.StatusOK, MDResponse{Name: mdName, Spec: md.Spec, Status: &md.Status})
}

// @Summary Get list of Model deployments
// @Description Get list of Model deployments
// @Tags ModelDeployment
// @Accept  json
// @Produce  json
// @Success 200 {array} v1.MDResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment [get]
func (controller *ModelDeploymentController) getAllMD(c *gin.Context) {
	var mdList v1alpha1.ModelDeploymentList
	selector, err := mapUrlParamsToLabels(c)
	if err != nil {
		logMD.Error(err, "Malformed url parameters")
		routes.AbortWithError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := controller.k8sClient.List(
		context.TODO(), &client.ListOptions{Namespace: controller.namespace, LabelSelector: selector}, &mdList,
	); err != nil {
		throwK8sError(c, err, "Retrieving list of md")
		return
	}

	mdEntities := make([]MDResponse, len(mdList.Items))
	for i := 0; i < len(mdList.Items); i++ {
		currentMD := mdList.Items[i]

		mdEntities[i] = MDResponse{Name: currentMD.Name, Spec: currentMD.Spec, Status: &currentMD.Status}
	}

	c.JSON(http.StatusOK, &mdEntities)
}

// @Summary Create a Model deployment
// @Description Create a Model deployment. Result is created Model deployment.
// @Param md body v1.MDRequest true "Create a Model deployment"
// @Tags ModelDeployment
// @Accept  json
// @Produce  json
// @Success 201 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment [post]
func (controller *ModelDeploymentController) createMD(c *gin.Context) {
	var mdEntity MDResponse

	if err := c.ShouldBindJSON(&mdEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	md := &v1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdEntity.Name,
			Namespace: controller.namespace,
		},
		Spec: mdEntity.Spec,
	}

	if err := controller.k8sClient.Create(context.TODO(), md); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Creation of the md: %+v", md))

		return
	}

	routes.AbortWithSuccess(c, http.StatusCreated, fmt.Sprintf("Model deployments %+v was created", mdEntity.Name))
}

// @Summary Update a Model deployment
// @Description Update a Model deployment. Result is updated Model deployment.
// @Param md body v1.MDRequest true "Update a Model deployment"
// @Tags ModelDeployment
// @Accept  json
// @Produce  json
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment [put]
func (controller *ModelDeploymentController) updateMD(c *gin.Context) {
	var mdEntity MDRequest

	if err := c.ShouldBindJSON(&mdEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	var md v1alpha1.ModelDeployment
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mdEntity.Name, Namespace: controller.namespace},
		&md,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Update md with name %s", mdEntity.Name))

		return
	}

	// TODO: think about update, not replacing as for now
	md.Spec = mdEntity.Spec

	if err := controller.k8sClient.Update(context.TODO(), &md); err != nil {
		logMD.Error(err, fmt.Sprintf("Creation of the md: %+v", md))
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model deployment %s was updated", md.Name))
}

// @Summary Delete a Model deployment
// @Description Delete a Model deployment by name
// @Tags ModelDeployment
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model deployment name"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment/{name} [delete]
func (controller *ModelDeploymentController) deleteMD(c *gin.Context) {
	mdName := c.Param("name")

	md := &v1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: controller.namespace,
		},
	}

	if err := controller.k8sClient.Delete(context.TODO(),
		md,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Dlete md with name %s", mdName))

		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model deployment %s was deleted", mdName))
}

// @Summary Delete list of Model deployments by labels
// @Description Delete list of Model deployments by labels
// @Tags ModelDeployment
// @Accept  json
// @Produce  json
// @Success 200 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/deployment [delete]
func (controller *ModelDeploymentController) deleteMDByLabels(c *gin.Context) {
	var mdList v1alpha1.ModelDeploymentList
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
		context.TODO(), &client.ListOptions{Namespace: controller.namespace, LabelSelector: selector}, &mdList,
	); err != nil {

		throwK8sError(c, err, "Retrieving list of md")
		return
	}

	if len(mdList.Items) == 0 {
		message := "Not found any model deployment elements. Skip deletion."
		logMD.Info(message)
		routes.AbortWithSuccess(c, http.StatusOK, message)

		return
	}

	// TODO: Need to parallelize
	for _, md := range mdList.Items {
		logMD.Info(fmt.Sprintf("Try to delete %s model deployment", md.Name))

		if err := controller.k8sClient.Delete(context.TODO(), &md); err != nil {
			logMD.Error(err, "Model deployment deletion")
			routes.AbortWithError(c, http.StatusOK, fmt.Sprintf("%s model deployment deletion is failed", md.Name))
		} else {
			logMD.Info(fmt.Sprintf("Deletion of %s model deployment finished successfully", md.Name))
		}
	}

	routes.AbortWithSuccess(c, http.StatusOK, "Model deployment were removed")
}
