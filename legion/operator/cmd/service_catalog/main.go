/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis"
	legion_config "github.com/legion-platform/legion/legion/operator/pkg/config"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	_ "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog/catalog"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog/controller"
	"github.com/spf13/cobra"
	_ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
	"os"
	"os/signal"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/runtime/signals"
	"syscall"
)

var log = logf.Log.WithName("service-catalog")

var mainCmd = &cobra.Command{
	Use:   "service-catalog",
	Short: "Legion service catalog server",
	Run: func(cmd *cobra.Command, args []string) {
		routeCatalog := catalog.NewModelRouteCatalog()

		log.Info("setting up client for manager")
		cfg, err := config.GetConfig()
		if err != nil {
			log.Error(err, "unable to set up client config")
			os.Exit(1)
		}

		log.Info("setting up manager")
		mgr, err := manager.New(
			cfg,
			manager.Options{
				//MetricsBindAddress: fmt.Sprintf(":%d", viper.GetInt(legion.PrometheusMetricsPort)),
			},
		)

		if err != nil {
			log.Error(err, "unable to set up overall controller manager")
			os.Exit(1)
		}

		log.Info("Registering Components.")

		log.Info("Setting up Legion scheme")
		if err := apis.AddToScheme(mgr.GetScheme()); err != nil {
			log.Error(err, "unable add Legion APIs to scheme")
			os.Exit(1)
		}

		log.Info("Setting up controller")
		if err := controller.AddToManager(mgr, routeCatalog); err != nil {
			log.Error(err, "unable to register controllers to the manager")
			os.Exit(1)
		}
		mainServer, err := service_catalog.SetUPMainServer(routeCatalog)

		if err != nil {
			log.Error(err, "Can't set up service-catalog server")
			os.Exit(1)
		}

		exitCh := make(chan int, 1)

		go func() {
			log.Info("Starting the operator.")
			if err := mgr.Start(signals.SetupSignalHandler()); err != nil {
				exitCh <- 1
			} else {
				exitCh <- 0
			}
		}()

		go func() {
			if err := mainServer.Run(":5000"); err != nil {
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
	},
}

func init() {
	legion_config.InitBasicParams(mainCmd)
}

func main() {
	if err := mainCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
