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
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
)

const (
	Namespace = "training.namespace"
	// Enable training API/operator
	Enabled                       = "training.enabled"
	ToolchainIntegrationNamespace = "training.ti_namespace"
	TrainingServiceAccount        = "training.service_account"
	OutputConnectionName          = "training.output_connection"
	ModelBuilderImage             = "training.model_trainer.image"
	NodeSelector                  = "training.node_selector"
	Toleration                    = "training.toleration"
	MetricURL                     = "training.metric_url"
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

	viper.SetDefault(Namespace, "legion-training")
	config.PanicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(TrainingServiceAccount, "legion-model-trainer")
	viper.SetDefault(ToolchainIntegrationNamespace, "legion")

	config.PanicIfError(viper.BindEnv(ModelBuilderImage))

	viper.SetDefault(NodeSelector, map[string]string{
		"mode": "legion-training",
	})

	viper.SetDefault(Toleration, map[string]string{
		TolerationKey:      "dedicated",
		TolerationOperator: "Equal",
		TolerationValue:    "training",
		TolerationEffect:   "NoSchedule",
	})

	viper.SetDefault(MetricURL, "")
}
