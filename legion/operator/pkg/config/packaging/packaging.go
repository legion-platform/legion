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
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
	"time"
)

const (
	Namespace = "packaging.namespace"
	// Enable packaging API/operator
	Enabled                       = "packaging.enabled"
	PackagingIntegrationNamespace = "packaging.packager_integration_namespace"
	ServiceAccount                = "packaging.service_account"
	OutputConnectionName          = "packaging.output_connection"
	ModelPackagerImage            = "packaging.model_packager.image"
	NodeSelector                  = "packaging.node_selector"
	Toleration                    = "packaging.toleration"
	Timeout                       = "packaging.timeout"
)

const (
	TolerationKey      = "Key"
	TolerationOperator = "Operator"
	TolerationValue    = "Value"
	TolerationEffect   = "Effect"
)

func init() {
	viper.SetDefault(Enabled, true)

	viper.SetDefault(Namespace, "legion-packaging")
	viper.SetDefault(PackagingIntegrationNamespace, "legion")
	config.PanicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(ServiceAccount, "legion-model-packager")
	viper.SetDefault(NodeSelector, map[string]string{
		"mode": "legion-packaging",
	})

	viper.SetDefault(Toleration, map[string]string{
		TolerationKey:      "dedicated",
		TolerationOperator: "Equal",
		TolerationValue:    "packaging",
		TolerationEffect:   "NoSchedule",
	})

	viper.SetDefault(Timeout, 60*time.Minute)
}
