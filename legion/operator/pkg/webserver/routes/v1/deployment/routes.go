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
	"github.com/gin-gonic/gin"
	md_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/deployment"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup, repository md_repository.Repository) {
	mdController := ModelDeploymentController{
		mdRepository: repository,
	}
	routeGroup.GET(GetModelDeploymentURL, mdController.getMD)
	routeGroup.GET(GetAllModelDeploymentURL, mdController.getAllMDs)
	routeGroup.POST(CreateModelDeploymentURL, mdController.createMD)
	routeGroup.PUT(UpdateModelDeploymentURL, mdController.updateMD)
	routeGroup.DELETE(DeleteModelDeploymentURL, mdController.deleteMD)

	mrController := ModelRouteController{
		mrRepository: repository,
		validator:    NewMrValidator(repository),
	}
	routeGroup.GET(GetModelRouteURL, mrController.getMR)
	routeGroup.GET(GetAllModelRouteURL, mrController.getAllMRs)
	routeGroup.POST(CreateModelRouteURL, mrController.createMR)
	routeGroup.PUT(UpdateModelRouteURL, mrController.updateMR)
	routeGroup.DELETE(DeleteModelRouteURL, mrController.deleteMR)
}
