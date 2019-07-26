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

package packaging_test

import (
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	mp_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/packaging"
	"sigs.k8s.io/controller-runtime/pkg/manager"

	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	mp_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging/kubernetes"

	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	conn_k8s_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"os"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"testing"
)

const (
	testNamespace = "default"
	testMpId1     = "test-model-1"
	testMpId2     = "test-model-2"
	mpTypeDocker  = "docker-rest"
	mpImage       = "docker-rest"
)

var (
	cfg            *rest.Config
	mpArtifactName = "mock-artifact-name-id"
	mpTargets      = []v1alpha1.Target{
		{
			Name:           "docker-push",
			ConnectionName: mpTypeDocker,
		},
	}
	mpArguments = map[string]interface{}{
		"key-1": "value-1",
		"key-2": float64(5),
		"key-3": true,
	}
	piArguments = packaging.JsonSchema{
		Properties: []packaging.Property{
			{
				Name: "argument-1",
				Parameters: []packaging.Parameter{
					{
						Name:  "minimum",
						Value: float64(5),
					},
					{
						Name:  "type",
						Value: "number",
					},
				},
			},
		},
		Required: []string{"argument-1"},
	}
	piTargets = []v1alpha1.TargetSchema{
		{
			Name: "target-1",
			ConnectionTypes: []string{
				string(connection.S3Type),
				string(connection.GcsType),
			},
			Required: false,
		},
		{
			Name: "target-2",
			ConnectionTypes: []string{
				string(connection.DockerType),
			},
			Required: true,
		},
	}
)

func TestMain(m *testing.M) {
	utils.SetupLogger()

	t := &envtest.Environment{
		CRDDirectoryPaths: []string{filepath.Join("..", "..", "..", "..", "..", "config", "crds")},
	}

	err := apis.AddToScheme(scheme.Scheme)
	if err != nil {
		panic(err)
	}

	cfg, err = t.Start()
	if err != nil {
		panic(err)
	}

	code := m.Run()
	err = t.Stop()
	if err != nil {
		panic(err)
	}
	os.Exit(code)
}

func createEnvironment() (*gin.Engine, mp_storage.Storage, conn_storage.Storage) {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	server := gin.Default()
	v1Group := server.Group("")
	storage := mp_k8s_storage.NewStorage(testNamespace, testNamespace, mgr.GetClient(), nil)
	connStorage := conn_k8s_storage.NewStorage(testNamespace, mgr.GetClient())
	mp_route.ConfigureRoutes(v1Group, storage, connStorage)

	return server, storage, connStorage
}

func newPackagingIntegration() *packaging.PackagingIntegration {
	return &packaging.PackagingIntegration{
		Id: piId,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   piEntrypoint,
			DefaultImage: piDefaultImage,
			Privileged:   piPrivileged,
			Schema: packaging.Schema{
				Targets:   piTargets,
				Arguments: piArguments,
			},
		},
	}
}
