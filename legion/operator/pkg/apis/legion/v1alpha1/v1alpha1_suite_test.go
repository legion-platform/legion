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

package v1alpha1

import (
	"context"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	"log"
	"os"
	"path/filepath"
	"testing"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
)

var cfg *rest.Config
var c client.Client

const (
	testNamespace = "default"
)

var (
	vcsTest = &VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "vcs-for-tests",
			Namespace: testNamespace,
		},
		Spec: VCSCredentialSpec{
			Type:             "git",
			Uri:              "git@github.com:legion-platform/legion.git",
			DefaultReference: "master",
			Credential:       "a2VrCg==",
		},
	}
	md1Test = &ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "md-1-for-tests",
			Namespace: testNamespace,
		},
		Spec: ModelDeploymentSpec{
			Image: "test/image:1",
		},
	}
	md2Test = &ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "md-2-for-tests",
			Namespace: testNamespace,
		},
		Spec: ModelDeploymentSpec{
			Image: "test/image:1",
		},
	}
)

func TestMain(m *testing.M) {
	t := &envtest.Environment{
		CRDDirectoryPaths: []string{filepath.Join("..", "..", "..", "..", "config", "crds")},
	}

	err := SchemeBuilder.AddToScheme(scheme.Scheme)
	if err != nil {
		log.Fatal(err)
	}

	if cfg, err = t.Start(); err != nil {
		log.Fatal(err)
	}

	if c, err = client.New(cfg, client.Options{Scheme: scheme.Scheme}); err != nil {
		log.Fatal(err)
	}

	viper.SetDefault(legion.Namespace, testNamespace)

	if err := c.Create(context.TODO(), vcsTest); err != nil {
		panic(err)
	}
	defer c.Delete(context.TODO(), vcsTest)

	if err := c.Create(context.TODO(), md1Test); err != nil {
		panic(err)
	}
	defer c.Delete(context.TODO(), md1Test)

	if err := c.Create(context.TODO(), md2Test); err != nil {
		panic(err)
	}
	defer c.Delete(context.TODO(), md2Test)

	code := m.Run()
	_ = t.Stop()

	os.Exit(code)
}
