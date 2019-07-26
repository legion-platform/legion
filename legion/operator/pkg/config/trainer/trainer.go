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

package trainer

import (
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
	"os"
	"path"
)

const (
	MTFile            = "trainer.mt_file"
	TargetPath        = "trainer.target_path"
	SSHKeyPath        = "trainer.ssh_key_path"
	OutputTrainingDir = "trainer.output_dir"
)

func init() {
	viper.SetDefault(SSHKeyPath, ".ssh/id_rsa")
	config.PanicIfError(viper.BindEnv(SSHKeyPath, ".ssh/id_rsa"))

	cwd, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	viper.SetDefault(TargetPath, path.Join(cwd, "legion/operator/target"))
	viper.SetDefault(OutputTrainingDir, path.Join(viper.GetString(TargetPath), "output"))
}
