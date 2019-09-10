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
	"github.com/gin-gonic/gin"
	connection_config "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	deployment_config "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	packaging_config "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	training_config "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	connection_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	deployment_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment/kubernetes"
	packaging_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging/kubernetes"
	training_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/training"
	"github.com/spf13/viper"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func SetupV1Routes(routeGroup *gin.RouterGroup, k8sClient client.Client, k8sConfig *rest.Config) {
	connStorage := connection_storage.NewStorage(viper.GetString(connection_config.Namespace), k8sClient)
	depStorage := deployment_storage.NewStorage(viper.GetString(deployment_config.Namespace), k8sClient)
	packStorage := packaging_storage.NewStorage(
		viper.GetString(packaging_config.Namespace),
		viper.GetString(packaging_config.PackagingIntegrationNamespace),
		k8sClient,
		k8sConfig,
	)
	trainStorage := training_storage.NewStorage(
		viper.GetString(training_config.Namespace),
		viper.GetString(training_config.ToolchainIntegrationNamespace),
		k8sClient,
		k8sConfig,
	)

	connection.ConfigureRoutes(routeGroup, connStorage)
	deployment.ConfigureRoutes(routeGroup, depStorage)
	packaging.ConfigureRoutes(routeGroup, packStorage, connStorage)
	training.ConfigureRoutes(routeGroup, trainStorage, connStorage)
}
