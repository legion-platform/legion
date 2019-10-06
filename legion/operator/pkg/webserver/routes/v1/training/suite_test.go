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

package training_test

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"os"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"testing"
)

const (
	testNamespace               = "default"
	testMtID                    = "test-mt"
	testMtID1                   = "test-mt-id-1"
	testMtID2                   = "test-mt-id-2"
	testModelVersion1           = "1"
	testModelVersion2           = "2"
	testModelName               = "test_name"
	testVcsReference            = "origin/develop123"
	testToolchainIntegrationID  = "ti"
	testToolchainIntegrationID1 = "ti-1"
	testToolchainIntegrationID2 = "ti-2"
	testMtEntrypoint            = "script.py"
	testMtVCSID                 = "legion-test"
	testToolchainMtImage        = "toolchain-image-test:123"
	testMtImage                 = "image-test:123"
	testMtReference             = "feat/123"
	testModelNameFilter         = "model_name"
	testModelVersionFilter      = "model_version"
	testMtDataPath              = "data/path"
)

var (
	cfg *rest.Config
)

func TestMain(m *testing.M) {
	utils.SetupLogger()

	t := &envtest.Environment{
		// Unit tests can be launched from any of directories because we use the relative path
		// We use the "legion/operator/config/crds" directory here
		CRDDirectoryPaths: []string{filepath.Join("..", "..", "..", "..", "..", "config", "crds")},
	}

	err := apis.AddToScheme(scheme.Scheme)
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	cfg, err = t.Start()
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}

	code := m.Run()
	err = t.Stop()
	if err != nil {
		// If we get a panic that we have a test configuration problem
		panic(err)
	}
	os.Exit(code)
}
