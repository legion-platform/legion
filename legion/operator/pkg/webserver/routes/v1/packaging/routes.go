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
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup, storage mp_storage.Storage, connStorage conn_storage.Storage) {
	mtController := ModelPackagingController{
		storage:   storage,
		validator: NewMpValidator(storage, connStorage),
	}
	routeGroup.GET(GetModelPackagingUrl, mtController.getMP)
	routeGroup.GET(GetAllModelPackagingUrl, mtController.getAllMPs)
	routeGroup.POST(CreateModelPackagingUrl, mtController.createMP)
	routeGroup.GET(GetModelPackagingLogsUrl, mtController.getModelPackagingLog)
	routeGroup.PUT(UpdateModelPackagingUrl, mtController.updateMP)
	routeGroup.DELETE(DeleteModelPackagingUrl, mtController.deleteMP)

	tiController := &PackagingIntegrationController{
		storage:   storage,
		validator: NewPiValidator(),
	}

	routeGroup.GET(getPackagingIntegrationUrl, tiController.getPackagingIntegration)
	routeGroup.GET(getAllPackagingIntegrationUrl, tiController.getAllPackagingIntegrations)
	routeGroup.POST(createPackagingIntegrationUrl, tiController.createPackagingIntegration)
	routeGroup.PUT(updatePackagingIntegrationUrl, tiController.updatePackagingIntegration)
	routeGroup.DELETE(deletePackagingIntegrationUrl, tiController.deletePackagingIntegration)
}
