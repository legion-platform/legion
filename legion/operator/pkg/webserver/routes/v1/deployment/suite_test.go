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

package deployment_test

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
	testNamespace = "default"
)

var (
	cfg *rest.Config
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
