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

package config

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	defaultConfigPathForDev = "legion/operator"
)

var (
	CfgFile string
	logC    = logf.Log.WithName("config")
)

func InitBasicParams(cmd *cobra.Command) {
	setUpLogger()
	cobra.OnInitialize(initConfig)

	cmd.Flags().StringVar(&CfgFile, "config", "", "config file")
}

func PanicIfError(err error) {
	if err != nil {
		panic(err)
	}
}

func initConfig() {
	if CfgFile != "" {
		viper.SetConfigFile(CfgFile)
	} else {
		viper.AddConfigPath(defaultConfigPathForDev)
	}

	if err := viper.ReadInConfig(); err != nil {
		logC.Error(err, "Reading config")
	}
}

func setUpLogger() {
	logf.SetLogger(logf.ZapLoggerTo(os.Stdout, true))
}
