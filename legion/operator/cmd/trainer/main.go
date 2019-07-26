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

package main

import (
	"fmt"
	trainer_conf "github.com/legion-platform/legion/legion/operator/pkg/config/trainer"
	train_conf "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	train_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"

	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/legion-platform/legion/legion/operator/pkg/trainer"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("trainer-main")

const (
	mtFile = "mt-file"
)

var mainCmd = &cobra.Command{
	Use:   "trainer",
	Short: "Legion trainer cli",
	Run: func(cmd *cobra.Command, args []string) {
		mgr, err := utils.NewManager()
		if err != nil {
			log.Error(err, "K8S manager creation failed")
		}

		modelBuilder, err := trainer.NewModelTrainer(
			train_k8s_storage.NewStorage(
				viper.GetString(train_conf.Namespace),
				viper.GetString(train_conf.ToolchainIntegrationNamespace),
				mgr.GetClient(), mgr.GetConfig(),
			),
		)

		if err != nil {
			log.Error(err, "Creation of model trainer failed")
			os.Exit(1)
		}

		if err := modelBuilder.Start(); err != nil {
			log.Error(err, "Build failed")
			os.Exit(1)
		}
	},
}

func init() {
	config.InitBasicParams(mainCmd)

	mainCmd.Flags().String(mtFile, "legion/operator/mt.json", "File with model training content")
	config.PanicIfError(viper.BindPFlag(trainer_conf.MTFile, mainCmd.Flags().Lookup(mtFile)))
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
