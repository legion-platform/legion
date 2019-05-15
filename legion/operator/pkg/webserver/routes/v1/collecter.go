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
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	"github.com/spf13/viper"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/selection"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func SetupV1Routes(routeGroup *gin.RouterGroup, k8sClient client.Client) {
	// VCS
	vcsController := VCSController{k8sClient: k8sClient, namespace: viper.GetString(legion.Namespace)}
	routeGroup.GET(getVcsUrl, vcsController.getVCS)
	routeGroup.GET(getAllVcsUrl, vcsController.getAllVCS)
	routeGroup.POST(createVcsUrl, vcsController.createVCS)
	routeGroup.PUT(updateVcsUrl, vcsController.updateVCS)
	routeGroup.DELETE(deleteVcsUrl, vcsController.deleteVCS)

	// ModelDeployment
	mdController := ModelDeploymentController{k8sClient: k8sClient, namespace: viper.GetString(legion.Namespace)}
	routeGroup.GET(getModelDeploymentUrl, mdController.getMD)
	routeGroup.GET(getAllModelDeploymentUrl, mdController.getAllMD)
	routeGroup.POST(createModelDeploymentUrl, mdController.createMD)
	routeGroup.PUT(updateModelDeploymentUrl, mdController.updateMD)
	routeGroup.DELETE(deleteModelDeploymentUrl, mdController.deleteMD)
	routeGroup.PUT(scaleModelDeploymentUrl, mdController.scaleMD)
	routeGroup.DELETE(deleteModelDeploymentByLabelsUrl, mdController.deleteMDByLabels)

	// ModelTraining
	mtController := ModelTrainingController{k8sClient: k8sClient, namespace: viper.GetString(legion.Namespace)}
	routeGroup.GET(getModelTrainingUrl, mtController.getMT)
	routeGroup.GET(getAllModelTrainingUrl, mtController.getAllMT)
	routeGroup.POST(createModelTrainingUrl, mtController.createMT)
	routeGroup.PUT(updateModelTrainingUrl, mtController.updateMT)
	routeGroup.DELETE(deleteModelTrainingUrl, mtController.deleteMT)
	routeGroup.DELETE(deleteModelTrainingByLabelsUrl, mtController.deleteMTByLabels)

	// Token
	routeGroup.POST(createModelJwt, generateToken)
}

// Pass through k8s error
func throwK8sError(c *gin.Context, err error, message string) {
	if errStatus, ok := err.(*k8serrors.StatusError); !ok {
		logVCS.Error(err, fmt.Sprintf("Type assertion error: %+v", err))
		routes.AbortWithError(c, 500, err.Error())
	} else {
		logVCS.Error(err, message)
		routes.AbortWithError(c, int(errStatus.ErrStatus.Code), err.Error())
	}
}

func mapUrlParamsToLabels(c *gin.Context) (selector labels.Selector, err error) {
	urlParameters := c.Request.URL.Query()
	labelSelector := labels.NewSelector()

	for name, value := range urlParameters {
		var operator selection.Operator
		if len(value) > 1 {
			operator = selection.In
		} else if len(value) == 1 {
			if value[0] == "*" {
				continue
			}
			operator = selection.Equals
		} else {
			return nil, errors.New(fmt.Sprintf("value of %s key must not contain zero length", name))
		}

		requirement, err := labels.NewRequirement(name, operator, value)
		if err != nil {
			return nil, err
		}

		labelSelector = labelSelector.Add(*requirement)
	}

	return labelSelector, nil
}
