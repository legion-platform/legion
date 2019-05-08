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

var logVCS = logf.Log.WithName("vcs-controller")

const (
	getVcsUrl    = "/vcs/:name"
	getAllVcsUrl = "/vcs"
	createVcsUrl = "/vcs"
	updateVcsUrl = "/vcs"
	deleteVcsUrl = "/vcs/:name"
)

type VCSController struct {
	k8sClient client.Client
	namespace string
}

type VCSEntity struct {
	// VCS name
	Name string `json:"name"`
	// VCS specification. It is the same as VCSCredential CRD specification
	Spec v1alpha1.VCSCredentialSpec `json:"spec"`
}

// @Summary Get a VCS Credential
// @Description Get a VCS Credential by name
// @Tags VCSCredential
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "VCS Credential name"
// @Success 200 {object} v1.VCSEntity
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/vcs/{name} [get]
func (controller *VCSController) getVCS(c *gin.Context) {
	vcsName := c.Param("name")

	var vcs v1alpha1.VCSCredential
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: vcsName, Namespace: controller.namespace},
		&vcs,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Retrieving vcs with name %s", vcsName))

		return
	}

	c.JSON(http.StatusOK, VCSEntity{Name: vcsName, Spec: vcs.Spec})
}

// @Summary Get list of VCS Credentials
// @Description Get list of VCS Credentials
// @Tags VCSCredential
// @Accept  json
// @Produce  json
// @Success 200 {array} v1.VCSEntity
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/vcs [get]
func (controller *VCSController) getAllVCS(c *gin.Context) {
	// TODO: Maybe we should add filters by labels
	var vcsList v1alpha1.VCSCredentialList

	if err := controller.k8sClient.List(context.TODO(), &client.ListOptions{Namespace: controller.namespace}, &vcsList); err != nil {
		throwK8sError(c, err, "Retrieving list of vcs")
		return
	}

	vcsEntities := make([]VCSEntity, len(vcsList.Items))
	for i := 0; i < len(vcsList.Items); i++ {
		currentVcs := vcsList.Items[i]

		vcsEntities[i] = VCSEntity{Name: currentVcs.Name, Spec: currentVcs.Spec}
	}

	c.JSON(http.StatusOK, &vcsEntities)
}

// @Summary Create a VCS Credential
// @Description Create a VCS Credential. Result is created VCS Credential.
// @Param vcs body v1.VCSEntity true "Create a VCS Credential"
// @Tags VCSCredential
// @Accept  json
// @Produce  json
// @Success 201 {object} v1.VCSEntity
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/vcs [post]
func (controller *VCSController) createVCS(c *gin.Context) {
	var vcsEntity VCSEntity

	if err := c.ShouldBindJSON(&vcsEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	vcs := &v1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsEntity.Name,
			Namespace: controller.namespace,
		},
		Spec: vcsEntity.Spec,
	}

	if err := controller.k8sClient.Create(context.TODO(), vcs); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Creation of the vcs: %+v", vcs))

		return
	}

	routes.AbortWithSuccess(c, http.StatusCreated, fmt.Sprintf("VCS Credentials %+v was created", vcsEntity.Name))
}

// @Summary Update a VCS Credential
// @Description Update a VCS Credential. Result is updated VCS Credential.
// @Param vcs body v1.VCSEntity true "Update a VCS Credential"
// @Tags VCSCredential
// @Accept  json
// @Produce  json
// @Success 201 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/vcs [put]
func (controller *VCSController) updateVCS(c *gin.Context) {
	var vcsEntity VCSEntity

	if err := c.ShouldBindJSON(&vcsEntity); err != nil {
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	var vcs v1alpha1.VCSCredential
	if err := controller.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: vcsEntity.Name, Namespace: controller.namespace},
		&vcs,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Update vcs with name %s", vcsEntity.Name))

		return
	}

	// TODO: think about update, not replacing as for now
	vcs.Spec = vcsEntity.Spec

	if err := controller.k8sClient.Update(context.TODO(), &vcs); err != nil {
		logVCS.Error(err, fmt.Sprintf("Creation of the vcs: %+v", vcs))
		routes.AbortWithError(c, 500, err.Error())
		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("VCS Credential %s was updated", vcs.Name))
}

// @Summary Delete a VCS Credential
// @Description Delete a VCS Credential by name
// @Tags VCSCredential
// @Name name
// @Accept  json
// @Produce  json
// @Param name path string true "VCS Credential name"
// @Success 200 {object} routes.HTTPResult
// @Failure 404 {object} routes.HTTPResult
// @Failure 500 {object} routes.HTTPResult
// @Router /api/v1/vcs/{name} [delete]
func (controller *VCSController) deleteVCS(c *gin.Context) {
	vcsName := c.Param("name")

	vcs := &v1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: controller.namespace,
		},
	}

	if err := controller.k8sClient.Delete(context.TODO(),
		vcs,
	); err != nil {
		throwK8sError(c, err, fmt.Sprintf("Dlete vcs with name %s", vcsName))

		return
	}

	routes.AbortWithSuccess(c, http.StatusOK, fmt.Sprintf("VCS Credential %s was deleted", vcsName))
}
