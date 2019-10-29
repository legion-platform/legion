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
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/feedback"
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/tapping"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	"os/signal"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"syscall"
)

const (
	cmdEnvoyHost      = "envoy-host"
	cmdEnvoyPort      = "envoy-port"
	cmdEnvoyConfigId  = "config-id"
	cmdMonitoringPort = "monitoring-port"
)

var log = logf.Log.WithName("collector-cmd")

var mainCmd = &cobra.Command{
	Use:   "collector",
	Short: "Envoy traffic collector",
	Run:   entrypoint,
}

func entrypoint(cmd *cobra.Command, args []string) {
	dataLogger, err := feedback.NewDataLogger()
	if err != nil {
		log.Error(err, "DataLogger creation")
		os.Exit(1)
	}

	defer dataLogger.Close()

	exitCh := make(chan int, 1)

	collector, err := tapping.NewRequestCollector(
		viper.GetString(tapping.CfgEnvoyHost),
		viper.GetInt(tapping.CfgEnvoyPort),
		viper.GetString(tapping.CfgEnvoyConfigId),
		dataLogger,
		viper.GetStringSlice(feedback.CfgProhibitedHeaders),
	)
	if err != nil {
		log.Error(err, "Collector creation")
		os.Exit(1)
	}

	go func() {
		if err := collector.TraceRequests(); err != nil {
			exitCh <- 1
		} else {
			exitCh <- 0
		}
	}()

	go func() {
		if err := tapping.StartMonitoringServer(); err != nil {
			exitCh <- 1
		} else {
			exitCh <- 0
		}
	}()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	select {
	case sig := <-sigs:
		log.Info("Getting signal. Stop", "signal", sig.String())
		os.Exit(0)
	case exitCode := <-exitCh:
		log.Info("Application stopped")
		os.Exit(exitCode)
	}
}

func init() {
	feedback.InitBasicParams(mainCmd)

	mainCmd.Flags().String(cmdEnvoyHost, "127.0.0.1", "Envoy host")
	mainCmd.Flags().Int(cmdEnvoyPort, 15000, "Envoy port")
	mainCmd.Flags().String(cmdEnvoyConfigId, "legion_feedback", "Envoy tap config id")

	feedback.PanicIfError(viper.BindPFlag(tapping.CfgEnvoyHost, mainCmd.Flags().Lookup(cmdEnvoyHost)))
	feedback.PanicIfError(viper.BindPFlag(tapping.CfgEnvoyPort, mainCmd.Flags().Lookup(cmdEnvoyPort)))
	feedback.PanicIfError(viper.BindPFlag(tapping.CfgEnvoyConfigId, mainCmd.Flags().Lookup(cmdEnvoyConfigId)))

	mainCmd.Flags().Int(cmdMonitoringPort, 7777, "Monitoring webserver port")
	feedback.PanicIfError(viper.BindPFlag(tapping.CfgMonitoringPort, mainCmd.Flags().Lookup(cmdMonitoringPort)))

	viper.SetConfigName("collector")
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
