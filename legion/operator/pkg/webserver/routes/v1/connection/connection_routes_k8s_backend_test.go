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

package connection_test

import (
	legion_apis "github.com/legion-platform/legion/legion/operator/pkg/apis"
	conn_k8s_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/stretchr/testify/suite"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"testing"
)

const (
	testNamespace = "default"
)

type ConnectionRouteK8sBackendSuite struct {
	ConnectionRouteGenericSuite
	k8sEnvironment *envtest.Environment
}

func (s *ConnectionRouteK8sBackendSuite) SetupSuite() {
	var cfg *rest.Config

	s.k8sEnvironment = &envtest.Environment{
		CRDDirectoryPaths: []string{filepath.Join("..", "..", "..", "..", "..", "config", "crds")},
	}

	err := legion_apis.AddToScheme(scheme.Scheme)
	if err != nil {
		s.T().Fatalf("Cannot setup the legion schema: %v", err)
	}

	cfg, err = s.k8sEnvironment.Start()
	if err != nil {
		s.T().Fatalf("Cannot setup the test k8s api: %v", err)
	}

	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		s.T().Fatalf("Cannot setup the test k8s manager: %v", err)
	}

	s.connDecryptToken = "some-token"
	s.connRepository = conn_k8s_repository.NewRepository(testNamespace, mgr.GetClient(), s.connDecryptToken)

	s.ConnectionRouteGenericSuite.SetupSuite()
}

func (s *ConnectionRouteK8sBackendSuite) TearDownSuite() {
	if err := s.k8sEnvironment.Stop(); err != nil {
		s.T().Fatal("Cannot stop the test k8s api")
	}
}

func TestConnectionRouteK8sBackend(t *testing.T) {
	suite.Run(t, new(ConnectionRouteK8sBackendSuite))
}
