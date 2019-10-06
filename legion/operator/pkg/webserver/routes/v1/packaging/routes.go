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
	"github.com/gin-gonic/gin"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup, repository mp_repository.Repository,
	connRepository conn_repository.Repository) {
	mtController := ModelPackagingController{
		repository: repository,
		validator:  NewMpValidator(repository, connRepository),
	}
	routeGroup.GET(GetModelPackagingURL, mtController.getMP)
	routeGroup.GET(GetAllModelPackagingURL, mtController.getAllMPs)
	routeGroup.POST(CreateModelPackagingURL, mtController.createMP)
	routeGroup.GET(GetModelPackagingLogsURL, mtController.getModelPackagingLog)
	routeGroup.PUT(UpdateModelPackagingURL, mtController.updateMP)
	routeGroup.DELETE(DeleteModelPackagingURL, mtController.deleteMP)

	tiController := &PackagingIntegrationController{
		repository: repository,
		validator:  NewPiValidator(),
	}

	routeGroup.GET(getPackagingIntegrationURL, tiController.getPackagingIntegration)
	routeGroup.GET(getAllPackagingIntegrationURL, tiController.getAllPackagingIntegrations)
	routeGroup.POST(createPackagingIntegrationURL, tiController.createPackagingIntegration)
	routeGroup.PUT(updatePackagingIntegrationURL, tiController.updatePackagingIntegration)
	routeGroup.DELETE(deletePackagingIntegrationURL, tiController.deletePackagingIntegration)
}
