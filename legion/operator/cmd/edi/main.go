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
	"os"

	"github.com/legion-platform/legion/legion/operator/pkg/config"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver"
	"github.com/spf13/cobra"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("edi")

var mainCmd = &cobra.Command{
	Use:   "edi",
	Short: "Legion EDI server",
	Run: func(cmd *cobra.Command, args []string) {
		mainServer, err := webserver.SetUPMainServer()
		if err != nil {
			log.Error(err, "Can't set up edi server")
			os.Exit(1)
		}

		if err := mainServer.Run(":5000"); err != nil {
			log.Error(err, "Server shutdowns")
			os.Exit(1)
		}
	},
}

func init() {
	config.InitBasicParams(mainCmd)
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
