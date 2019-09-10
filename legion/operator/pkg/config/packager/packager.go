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
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
	"os"
	"path"
)

const (
	MPFile            = "packager.mt_file"
	TargetPath        = "packager.target_path"
	OutputTrainingDir = "packager.output_dir"
	PodName           = "packager.pod_name"
)

func init() {
	cwd, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	viper.SetDefault(TargetPath, path.Join(cwd, "legion/operator/target"))
	viper.SetDefault(OutputTrainingDir, path.Join(viper.GetString(TargetPath), "output"))

	viper.SetDefault(PodName, "test-pod-name")
	config.PanicIfError(viper.BindEnv(PodName))
}
