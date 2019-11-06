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

package vault

import (
	"github.com/hashicorp/vault/api"
	"github.com/hashicorp/vault/http"
	"github.com/hashicorp/vault/vault"
	"net"
	"testing"
)

func CreateTestVault(t *testing.T, mountPath, mountEngine string) (*api.Client, net.Listener) {
	// Create an in-memory, unsealed core (the "backend", if you will).
	core, _, rootToken := vault.TestCoreUnsealed(t)

	// Start an HTTP server for the core.
	server, addr := http.TestServer(t, core)

	// Create a client that talks to the server, initially authenticating with
	// the root token.
	conf := api.DefaultConfig()
	conf.Address = addr

	// Let's enable KV secret engine for `/test` path
	client, err := api.NewClient(conf)
	if err != nil {
		t.Fatal("Cannot initialize client for test vault server")
	}
	client.SetToken(rootToken)
	err = client.Sys().Mount(mountPath, &api.MountInput{
		Type: mountEngine,
	})
	if err != nil {
		t.Fatal("Cannot create secret engine mount for test vault server")
	}

	return client, server
}
