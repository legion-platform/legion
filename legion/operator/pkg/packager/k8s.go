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

package packager

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	packaging_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
)

func PackOnk8sContainer(mpFilePath string, packaging *packaging.K8sPackager) error {
	clientConfig, err := utils.GetClientConfig()
	if err != nil {
		return err
	}

	commands := []string{
		"bash",
		"-c",
		fmt.Sprintf("cd %s && %s %s %s",
			viper.GetString(packager_conf.TargetPath),
			packaging.PackagingIntegration.Spec.Entrypoint,
			viper.GetString(packager_conf.OutputTrainingDir), mpFilePath,
		),
	}
	return utils.ExecToPodThroughAPI(commands, "model", viper.GetString(packager_conf.PodName),
		viper.GetString(packaging_conf.Namespace), clientConfig)
}
