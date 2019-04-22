package utils

import (
	_ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/cache"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"

	"github.com/legion-platform/legion/legion/operator/pkg/apis"
)

var logManager = logf.Log.WithName("k8s-manager")

func NewClient(cache cache.Cache, config *rest.Config, options client.Options) (client.Client, error) {
	c, err := client.New(config, options)
	if err != nil {
		return nil, err
	}

	// TODO: enable caching for k8s entities
	return &client.DelegatingClient{
		Reader:       c,
		Writer:       c,
		StatusClient: c,
	}, nil
}

func NewManager() (manager.Manager, error) {
	cfg, err := config.GetConfig()
	if err != nil {
		logManager.Error(err, "K8s config creation")
		return nil, err
	}

	mgr, err := manager.New(cfg, manager.Options{NewClient: NewClient})
	if err != nil {
		logManager.Error(err, "Manager creation")
		return nil, err
	}

	if err := apis.AddToScheme(mgr.GetScheme()); err != nil {
		logManager.Error(err, "Update schema")
		return nil, err
	}

	return mgr, nil
}
