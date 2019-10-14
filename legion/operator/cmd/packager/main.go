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
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	pack_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	pack_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"

	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/legion-platform/legion/legion/operator/pkg/packager"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("packager-main")

const (
	mpFile = "mp-file"
)

var mainCmd = &cobra.Command{
	Use:              "packager",
	Short:            "Legion packager cli",
	TraverseChildren: true,
}

var packagerSetupCmd = &cobra.Command{
	Use:   "setup",
	Short: "Prepare environment for a packager",
	Run: func(cmd *cobra.Command, args []string) {
		if err := packager.SetupPackager(); err != nil {
			log.Error(err, "Setup failed")
			os.Exit(1)
		}
	},
}

var saveCmd = &cobra.Command{
	Use:   "save",
	Short: "Save a packer result",
	Run: func(cmd *cobra.Command, args []string) {
		mgr, err := utils.NewManager()
		if err != nil {
			log.Error(err, "K8S manager creation failed")
		}

		repository := pack_k8s_storage.NewRepository(
			viper.GetString(pack_conf.Namespace),
			viper.GetString(pack_conf.PackagingIntegrationNamespace),
			mgr.GetClient(), mgr.GetConfig(),
		)

		if err := packager.SaveResult(repository); err != nil {
			log.Error(err, "Result saving failed")
			os.Exit(1)
		}
	},
}

func init() {
	config.InitBasicParams(mainCmd)

	mainCmd.PersistentFlags().String(mpFile, "legion/operator/mp.json", "File with model packaging content")
	config.PanicIfError(viper.BindPFlag(packager_conf.MPFile, mainCmd.PersistentFlags().Lookup(mpFile)))

	mainCmd.AddCommand(packagerSetupCmd, saveCmd)
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
