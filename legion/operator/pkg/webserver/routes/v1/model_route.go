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

var logMR = logf.Log.WithName("mr-controller")

const (
	getModelRouteUrl    = "/model/route/:name"
	getAllModelRouteUrl = "/model/route"
	createModelRouteUrl = "/model/route"
	updateModelRouteUrl = "/model/route"
	deleteModelRouteUrl = "/model/route/:name"
)

type ModelRouteController struct {
	k8sClient client.Client
	namespace string
}

type MRRequest struct {
	// Model route name
	Name string `json:"name"`
	// Model Route specification. It is the same as ModelRoute CRD specification
	Spec v1alpha1.ModelRouteSpec `json:"spec"`
}

type MRResponse struct {
	// Model route name
	Name string `json:"name"`
	// Model Route specification. It is the same as ModelRoute CRD specification
	Spec v1alpha1.ModelRouteSpec `json:"spec"`
	// Model Route specification. It is the same as ModelRoute CRD specification
	Status *v1alpha1.ModelRouteStatus `json:"status,omitempty"`
}

// @Summary Get a Model route
// @Description Get a Model route by name
// @Tags ModelRoute
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model route name"
// @Success 200 {object} v1.MRResponse
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/route/{name} [get]
func (controller *ModelRouteController) getMR(c *gin.Context) {
	mrName := c.Param("name")

	var mr v1alpha1.ModelRoute
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mrName, Namespace: controller.namespace},
		&mr,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Retrieving mr with name %s", mrName))

		return
	}

	c.JSON(http.StatusOK, MRResponse{Name: mrName, Spec: mr.Spec, Status: &mr.Status})
}

// @Summary Get list of Model routes
// @Description Get list of Model routes
// @Tags ModelRoute
// @Accept  json
// @Produce  json
// @Success 200 {array} v1.MRResponse
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/route [get]
func (controller *ModelRouteController) getAllMR(c *gin.Context) {
	var mrList v1alpha1.ModelRouteList
	selector, err := mapUrlParamsToLabels(c)
	if err != nil {
		logMR.Error(err, "Malformed url parameters")
		routes.AbortWithError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := controller.k8sClient.List(
		context.TODO(), &client.ListOptions{Namespace: controller.namespace, LabelSelector: selector}, &mrList,
	); err != nil {
		throwK8sError(c, err, "Retrieving list of mr")
		return
	}

	mrEntities := make([]MRResponse, len(mrList.Items))
	for i := 0; i < len(mrList.Items); i++ {
		currentMR := mrList.Items[i]

		mrEntities[i] = MRResponse{Name: currentMR.Name, Spec: currentMR.Spec, Status: &currentMR.Status}
	}

	c.JSON(http.StatusOK, &mrEntities)
}

// @Summary Create a Model route
// @Description Create a Model route. Result is created Model route.
// @Param mr body v1.MRRequest true "Create a Model route"
// @Tags ModelRoute
// @Accept  json
// @Produce  json
// @Success 201 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/route [post]
func (controller *ModelRouteController) createMR(c *gin.Context) {
	var mrEntiry MRResponse

	if err := c.ShouldBindJSON(&mrEntiry); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	mr := &v1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrEntiry.Name,
			Namespace: controller.namespace,
		},
		Spec: mrEntiry.Spec,
	}

	if err := controller.k8sClient.Create(context.TODO(), mr); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Creation of the mr: %+v", mr))

		return
	}

	routes.AbortWithSuccess(c, http.StatusCreated, fmt.Sprintf("Model routes %+v was created", mrEntiry.Name))
}

// @Summary Update a Model route
// @Description Update a Model route. Result is updated Model route.
// @Param mr body v1.MDRequest true "Update a Model route"
// @Tags ModelRoute
// @Accept  json
// @Produce  json
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/route [put]
func (controller *ModelRouteController) updateMR(c *gin.Context) {
	var mrEntiry MRRequest

	if err := c.ShouldBindJSON(&mrEntiry); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	var mr v1alpha1.ModelRoute
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mrEntiry.Name, Namespace: controller.namespace},
		&mr,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Update mr with name %s", mrEntiry.Name))

		return
	}

	// TODO: think about update, not replacing as for now
	mr.Spec = mrEntiry.Spec

	if err := controller.k8sClient.Update(context.TODO(), &mr); err != nil {
		logMD.Error(err, fmt.Sprintf("Creation of the mr: %+v", mr))
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model route %s was updated", mr.Name))
}

// @Summary Delete a Model route
// @Description Delete a Model route by name
// @Tags ModelRoute
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "Model route name"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/model/route/{name} [delete]
func (controller *ModelRouteController) deleteMR(c *gin.Context) {
	mrName := c.Param("name")

	mr := &v1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: controller.namespace,
		},
	}

	if err := controller.k8sClient.Delete(context.TODO(),
		mr,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Dlete mr with name %s", mrName))

		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("Model route %s was deleted", mrName))
}
