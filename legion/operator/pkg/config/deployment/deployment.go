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
	Namespace                = "deployment.namespace"
	DefaultRoleName          = "deployment.security.role_name"
	SecurityJwtEnabled       = "deployment.security.jwt.enabled"
	SecurityJwtPrivateKey    = "deployment.security.jwt.private_key"
	SecurityJwtPublicKey     = "deployment.security.jwt.public_key"
	SecurityJwtExpDatetime   = "deployment.security.jwt.exp_date_time"
	SecurityJwtMaxTtlMinutes = "deployment.security.jwt.max_ttl_min"
	SecurityJwtTtlMinutes    = "deployment.security.jwt.ttl_minute"
	SecurityJwksUrl          = "deployment.security.jwks.url"
	SecurityJwksCluster      = "deployment.security.jwks.cluster"
	ModelLogsFlushSize       = "deployment.model_log.flush_size"
	ServerTemplateFolder     = "deployment.server.template_folder"
	EdgeHost                 = "deployment.edge.host"
	NodeSelector             = "deployment.node_selector"
	Toleration               = "deployment.toleration"
)

const (
	TolerationKey      = "Key"
	TolerationOperator = "Operator"
	TolerationValue    = "Value"
	TolerationEffect   = "Effect"
)

func init() {
	viper.SetDefault(DefaultRoleName, "default-legion")
	config.PanicIfError(viper.BindEnv(DefaultRoleName))

	viper.SetDefault(Namespace, "legion-deployment")
	config.PanicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(SecurityJwtTtlMinutes, 120)
	config.PanicIfError(viper.BindEnv(SecurityJwtTtlMinutes))

	viper.SetDefault(SecurityJwtEnabled, false)
	config.PanicIfError(viper.BindEnv(SecurityJwtEnabled))

	viper.SetDefault(SecurityJwtMaxTtlMinutes, 259200)
	config.PanicIfError(viper.BindEnv(SecurityJwtMaxTtlMinutes))

	viper.SetDefault(SecurityJwtExpDatetime, "")
	config.PanicIfError(viper.BindEnv(SecurityJwtExpDatetime))

	viper.SetDefault(ModelLogsFlushSize, 32)
	config.PanicIfError(viper.BindEnv(ModelLogsFlushSize))

	viper.SetDefault(SecurityJwtPrivateKey, "legion/operator/private_key.pem")
	config.PanicIfError(viper.BindEnv(SecurityJwtPrivateKey))

	viper.SetDefault(SecurityJwtPublicKey, "legion/operator/public_key.pem")
	config.PanicIfError(viper.BindEnv(SecurityJwtPublicKey))

	viper.SetDefault(ServerTemplateFolder, "legion/operator/templates")
	config.PanicIfError(viper.BindEnv(ServerTemplateFolder))

	viper.SetDefault(SecurityJwksUrl, "http://legion-edi.legion.svc.cluster.local/api/v1/model/jwks")
	config.PanicIfError(viper.BindEnv(SecurityJwksUrl))

	viper.SetDefault(SecurityJwksCluster, "outbound|80||legion-edi.legion.svc.cluster.local")
	config.PanicIfError(viper.BindEnv(SecurityJwksCluster))

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
}
