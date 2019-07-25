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
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/aggregator"
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/feedback"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	cmdPort = "port"
)

var log = logf.Log.WithName("aggregator-cmd")

var mainCmd = &cobra.Command{
	Use:   "feedback-aggregator",
	Short: "Legion feedback aggregator server",
	Run: func(cmd *cobra.Command, args []string) {
		dataLogger, err := feedback.NewDataLogger()
		if err != nil {
			log.Error(err, "DataLogger creation")
			os.Exit(1)
		}

		defer dataLogger.Close()

		err = aggregator.StartServer(dataLogger)
		if err != nil {
			log.Error(err, "Server exit")
			os.Exit(1)
		}
	},
}

func init() {
	feedback.InitBasicParams(mainCmd)

	viper.SetConfigName("aggregator")

	mainCmd.Flags().Int(cmdPort, 8080, "Monitoring webserver port")
	feedback.PanicIfError(viper.BindPFlag(aggregator.CfgPort, mainCmd.Flags().Lookup(cmdPort)))
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
