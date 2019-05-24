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

	istioschema "github.com/aspenmesh/istio-client-go/pkg/client/clientset/versioned/scheme"
	knservingv1alpha1 "github.com/knative/serving/pkg/apis/serving/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis"
	"github.com/legion-platform/legion/legion/operator/pkg/controller"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	_ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
	"os"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/runtime/signals"
)

func main() {
	logf.SetLogger(logf.ZapLogger(true))
	log := logf.Log.WithName("entrypoint")

	legion.SetUpOperatorConfig()

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
			MetricsBindAddress: fmt.Sprintf(":%d", viper.GetInt(legion.PrometheusMetricsPort)),
		},
	)
	if err != nil {
		log.Error(err, "unable to set up overall controller manager")
		os.Exit(1)
	}

	log.Info("Registerifng Components.")

	log.Info("Setting up Legion scheme")
	if err := apis.AddToScheme(mgr.GetScheme()); err != nil {
		log.Error(err, "unable add Legion APIs to scheme")
		os.Exit(1)
	}

	log.Info("Setting up Istio scheme")
	istioschema.AddToScheme(mgr.GetScheme())

	log.Info("Setting up Knative scheme")
	if err := knservingv1alpha1.AddToScheme(mgr.GetScheme()); err != nil {
		log.Error(err, "unable add Knative APIs to scheme")
		os.Exit(1)
	}

	log.Info("Setting up controller")
	if err := controller.AddToManager(mgr); err != nil {
		log.Error(err, "unable to register controllers to the manager")
		os.Exit(1)
	}

	log.Info("Starting the operator.")
	if err := mgr.Start(signals.SetupSignalHandler()); err != nil {
		log.Error(err, "unable to run the manager")
		os.Exit(1)
	}
}
