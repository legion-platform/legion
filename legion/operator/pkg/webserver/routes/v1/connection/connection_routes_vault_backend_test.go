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
	conn_vault_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection/vault"
	legion_vault_utils "github.com/legion-platform/legion/legion/operator/pkg/repository/util/vault"
	"github.com/stretchr/testify/suite"
	"net"
	"testing"
)

const (
	testSecretMountPath   = "test-path"
	testSecretMountEngine = "kv"
	testDecryptToken      = "test-decrypt-token" //nolint
)

type ConnectionRouteVaultBackendSuite struct {
	ConnectionRouteGenericSuite
	vaultServer net.Listener
}

func (s *ConnectionRouteVaultBackendSuite) SetupSuite() {
	vaultClient, vaultServer := legion_vault_utils.CreateTestVault(
		s.T(),
		testSecretMountPath,
		testSecretMountEngine,
	)

	s.connRepository = conn_vault_repository.NewRepository(vaultClient, testSecretMountPath, testDecryptToken)
	s.vaultServer = vaultServer
	s.connDecryptToken = testDecryptToken

	s.ConnectionRouteGenericSuite.SetupSuite()
}

func (s *ConnectionRouteVaultBackendSuite) TearDownSuite() {
	err := s.vaultServer.Close()
	if err != nil {
		s.T().Fatal("Cannot shutdown test vault server")
	}
}

func TestConnectionRouteVaultBackend(t *testing.T) {
	suite.Run(t, new(ConnectionRouteVaultBackendSuite))
}
