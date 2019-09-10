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
	"github.com/gin-gonic/gin"
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	mt_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
)

func ConfigureRoutes(routeGroup *gin.RouterGroup, mtStorage mt_storage.Storage, connStorage conn_storage.Storage) {
	mtController := ModelTrainingController{
		mtStorage: mtStorage,
		validator: NewMtValidator(mtStorage, connStorage),
	}
	routeGroup.GET(GetModelTrainingUrl, mtController.getMT)
	routeGroup.GET(GetAllModelTrainingUrl, mtController.getAllMTs)
	routeGroup.GET(GetModelTrainingLogsUrl, mtController.getModelTrainingLog)
	routeGroup.POST(CreateModelTrainingUrl, mtController.createMT)
	routeGroup.PUT(UpdateModelTrainingUrl, mtController.updateMT)
	routeGroup.DELETE(DeleteModelTrainingUrl, mtController.deleteMT)

	tiController := &ToolchainIntegrationController{
		storage:   mtStorage,
		validator: NewTiValidator(),
	}

	routeGroup.GET(GetToolchainIntegrationUrl, tiController.getToolchainIntegration)
	routeGroup.GET(GetAllToolchainIntegrationUrl, tiController.getAllToolchainIntegrations)
	routeGroup.POST(CreateToolchainIntegrationUrl, tiController.createToolchainIntegration)
	routeGroup.PUT(UpdateToolchainIntegrationUrl, tiController.updateToolchainIntegration)
	routeGroup.DELETE(DeleteToolchainIntegrationUrl, tiController.deleteToolchainIntegration)
}
