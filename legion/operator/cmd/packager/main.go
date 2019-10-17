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
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	"github.com/legion-platform/legion/legion/operator/pkg/packager"
	connection_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/http"
	packaging_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/http"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("packager-main")

const (
	mpFileCLIParam               = "mp-file"
	mpIDCLIParam                 = "mp-id"
	outputConnectionNameCLIParam = "output-connection-name"
	ediURLCLIParam               = "edi-url"
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
		if err := newPackagerWithHTTPRepositories().SetupPackager(); err != nil {
			log.Error(err, "Packaging setup failed")
			os.Exit(1)
		}
	},
}

var saveCmd = &cobra.Command{
	Use:   "result",
	Short: "Save a packer result",
	Run: func(cmd *cobra.Command, args []string) {
		if err := newPackagerWithHTTPRepositories().SaveResult(); err != nil {
			log.Error(err, "Result saving failed")
			os.Exit(1)
		}
	},
}

func init() {
	config.InitBasicParams(mainCmd)

	mainCmd.PersistentFlags().String(mpFileCLIParam, "mp.json", "File with model packaging content")
	config.PanicIfError(viper.BindPFlag(packager_conf.MPFile, mainCmd.PersistentFlags().Lookup(mpFileCLIParam)))

	mainCmd.PersistentFlags().String(mpIDCLIParam, "", "ID of the model packaging")
	config.PanicIfError(viper.BindPFlag(packager_conf.ModelPackagingID, mainCmd.PersistentFlags().Lookup(mpIDCLIParam)))

	mainCmd.PersistentFlags().String(ediURLCLIParam, "", "EDI URL")
	config.PanicIfError(viper.BindPFlag(packager_conf.EdiURL, mainCmd.PersistentFlags().Lookup(ediURLCLIParam)))

	mainCmd.PersistentFlags().String(outputConnectionNameCLIParam,
		"It is a connection ID, which specifies where a artifact trained artifact is stored.",
		"File with model packaging content",
	)
	config.PanicIfError(viper.BindPFlag(
		packager_conf.OutputConnectionName,
		mainCmd.PersistentFlags().Lookup(outputConnectionNameCLIParam)),
	)

	mainCmd.AddCommand(packagerSetupCmd, saveCmd)
}

func newPackagerWithHTTPRepositories() *packager.Packager {
	packRepo := packaging_http_repository.NewRepository(
		viper.GetString(packager_conf.EdiURL), viper.GetString(packager_conf.EdiToken),
	)
	connRepo := connection_http_repository.NewRepository(
		viper.GetString(packager_conf.EdiURL), viper.GetString(packager_conf.EdiToken),
	)

	return packager.NewPackager(packRepo, connRepo, viper.GetString(packager_conf.ModelPackagingID))
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		log.Error(err, "packager CLI command failed")

		os.Exit(1)
	}
}
