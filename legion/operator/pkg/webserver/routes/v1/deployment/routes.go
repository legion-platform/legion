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
	md_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup, storage md_storage.Storage) {
	mdController := ModelDeploymentController{
		mdStorage: storage,
	}
	routeGroup.GET(GetModelDeploymentUrl, mdController.getMD)
	routeGroup.GET(GetAllModelDeploymentUrl, mdController.getAllMDs)
	routeGroup.POST(CreateModelDeploymentUrl, mdController.createMD)
	routeGroup.PUT(UpdateModelDeploymentUrl, mdController.updateMD)
	routeGroup.DELETE(DeleteModelDeploymentUrl, mdController.deleteMD)

	mrController := ModelRouteController{
		mrStorage: storage,
		validator: NewMrValidator(storage),
	}
	routeGroup.GET(GetModelRouteUrl, mrController.getMR)
	routeGroup.GET(GetAllModelRouteUrl, mrController.getAllMRs)
	routeGroup.POST(CreateModelRouteUrl, mrController.createMR)
	routeGroup.PUT(UpdateModelRouteUrl, mrController.updateMR)
	routeGroup.DELETE(DeleteModelRouteUrl, mrController.deleteMR)
}
