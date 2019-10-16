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
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
)

const (
	Namespace = "deployment.namespace"
	// Enable deployment API/operator
	Enabled         = "deployment.enabled"
	DefaultRoleName = "deployment.security.role_name"
	// Jwks url for mode authorization
	SecurityJwksURL = "deployment.security.jwks.url"
	// The Issuer Identifier for mode authorization
	SecurityJwksIssuer = "deployment.security.jwks.issuer"
	// Is model authorization enabled
	SecurityJwksEnabled  = "deployment.security.jwks.enabled"
	ModelLogsFlushSize   = "deployment.model_log.flush_size"
	ServerTemplateFolder = "deployment.server.template_folder"
	EdgeHost             = "deployment.edge.host"
	NodeSelector         = "deployment.node_selector"
	Toleration           = "deployment.toleration"
	IstioServiceName     = "deployment.istio.service_name"
	IstioNamespace       = "deployment.istio.namespace"
)

const (
	TolerationKey      = "Key"
	TolerationOperator = "Operator"
	TolerationValue    = "Value"
	TolerationEffect   = "Effect"
)

func init() {
	viper.SetDefault(Enabled, true)

	viper.SetDefault(DefaultRoleName, "default-legion")
	config.PanicIfError(viper.BindEnv(DefaultRoleName))

	viper.SetDefault(Namespace, "legion-deployment")
	config.PanicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(ModelLogsFlushSize, 32)
	config.PanicIfError(viper.BindEnv(ModelLogsFlushSize))

	viper.SetDefault(ServerTemplateFolder, "legion/operator/templates")
	config.PanicIfError(viper.BindEnv(ServerTemplateFolder))

	viper.SetDefault(SecurityJwksURL, "")
	config.PanicIfError(viper.BindEnv(SecurityJwksURL))

	viper.SetDefault(SecurityJwksIssuer, "")
	config.PanicIfError(viper.BindEnv(SecurityJwksIssuer))

	viper.SetDefault(SecurityJwksEnabled, false)
	config.PanicIfError(viper.BindEnv(SecurityJwksEnabled))

	viper.SetDefault(EdgeHost, "")
	config.PanicIfError(viper.BindEnv(EdgeHost))

	viper.SetDefault(NodeSelector, map[string]string{
		"mode": "legion-deployment",
	})

	viper.SetDefault(Toleration, map[string]string{
		TolerationKey:      "dedicated",
		TolerationOperator: "Equal",
		TolerationValue:    "deployment",
		TolerationEffect:   "NoSchedule",
	})

	viper.SetDefault(IstioServiceName, "istio-ingressgateway")
	viper.SetDefault(IstioNamespace, "istio-system")
}
