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

package connection

import (
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
)

const (
	Namespace = "connection.namespace"
	// Enable connection API/operator
	Enabled = "connection.enabled"
)

func init() {
	viper.SetDefault(Enabled, true)

	viper.SetDefault(Namespace, "legion")
	config.PanicIfError(viper.BindEnv(Namespace))
}
