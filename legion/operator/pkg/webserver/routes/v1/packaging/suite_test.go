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

	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	mp_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/kubernetes"

	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	conn_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"os"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"testing"
)

const (
	testNamespace = "default"
	testMpID1     = "test-model-1"
	testMpID2     = "test-model-2"
	mpImage       = "docker-rest"
)

var (
	cfg            *rest.Config
	mpArtifactName = "mock-artifact-name-id"
	piArguments    = packaging.JsonSchema{
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
				string(connection.AzureBlobType),
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

func createEnvironment() (*gin.Engine, mp_repository.Repository, conn_repository.Repository) {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	server := gin.Default()
	v1Group := server.Group("")
	repository := mp_k8s_repository.NewRepository(testNamespace, testNamespace, mgr.GetClient(), nil)
	connRepository := conn_k8s_repository.NewRepository(testNamespace, mgr.GetClient())
	mp_route.ConfigureRoutes(v1Group, repository, connRepository)

	return server, repository, connRepository
}

func newPackagingIntegration() *packaging.PackagingIntegration {
	return &packaging.PackagingIntegration{
		ID: piID,
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
