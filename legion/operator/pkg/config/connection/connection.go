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

package connection

import (
	"github.com/legion-platform/legion/legion/operator/pkg/config"
	"github.com/spf13/viper"
)

const (
	Namespace = "connection.namespace"
	// Enable connection API/operator
	Enabled = "connection.enabled"
	// Storage backend for connections. Available options:
	//   * kubernetes
	//   * vault
	RepositoryType = "connection.repository_type"
	// TODO: Remove after implementation of the issue https://github.com/legion-platform/legion/issues/1008
	DecryptToken = "connection.decrypt_token"
	// Vault URL
	VaultURL = "connection.vault.url"
	// Vault secret engine path where connection will be stored
	VaultSecretEnginePath = "connection.vault.secret_engine_path"
	// Vault role for access to the secret engine path
	VaultRole = "connection.vault.role"
	// Optionally. Token for access to the vault server
	// If it is empty then client will use the k8s auth
	VaultToken = "connection.vault.token"

	RepositoryKubernetesType = "kubernetes"
	RepositoryVaultType      = "vault"
)

func init() {
	viper.SetDefault(Enabled, true)

	viper.SetDefault(Namespace, "legion")
	config.PanicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(VaultToken, "")
	// This is url of local vault in dev mode
	viper.SetDefault(VaultURL, "http://127.0.0.1:8200")
	viper.SetDefault(VaultSecretEnginePath, "legion/connections")
	viper.SetDefault(VaultRole, "legion")

	viper.SetDefault(RepositoryType, RepositoryKubernetesType)
}
