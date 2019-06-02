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

package v1

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/apis"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"sigs.k8s.io/controller-runtime/pkg/manager"

	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"os"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"testing"
)

const (
	testNamespace              = "default"
	testDockerRegistryUser     = "test_user"
	testDockerRegistryPassword = "test_password"
	testModelVersion1          = "1"
	testModelVersion2          = "2"
	testModelId                = "id"
)

var (
	cfg            *rest.Config
	testModelName1 = fmt.Sprintf("%s-1", mdName)
	testModelName2 = fmt.Sprintf("%s-2", mdName)
)

func TestMain(m *testing.M) {
	utils.SetupLogger()

	t := &envtest.Environment{
		CRDDirectoryPaths: []string{filepath.Join("..", "..", "..", "..", "config", "crds")},
	}

	err := apis.AddToScheme(scheme.Scheme)
	if err != nil {
		panic(err)
	}

	cfg, err = t.Start()
	if err != nil {
		panic(err)
	}

	SetupConfig()

	code := m.Run()
	err = t.Stop()
	if err != nil {
		panic(err)
	}
	os.Exit(code)
}

func SetupConfig() {
	viper.Set(legion.Namespace, testNamespace)
	viper.Set(legion.DockerRegistryUser, testDockerRegistryUser)
	viper.Set(legion.DockerRegistryPassword, testDockerRegistryPassword)
}

func createEnvironment() (*gin.Engine, client.Client) {
	mgr, err := manager.New(cfg, manager.Options{NewClient: utils.NewClient})
	if err != nil {
		panic(err)
	}

	server := gin.Default()
	v1Group := server.Group("/api/v1")
	k8Client := mgr.GetClient()
	SetupV1Routes(v1Group, k8Client, mgr.GetConfig())

	return server, k8Client
}

func createModelDeployments(g *GomegaWithT, c client.Client) []*legionv1alpha1.ModelDeployment {
	md1 := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      testModelName1,
			Namespace: testNamespace,
			Labels: map[string]string{
				legion.DomainModelId:      testModelId,
				legion.DomainModelVersion: testModelVersion1,
			},
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   &mdReplicas,
			LivenessProbeInitialDelay:  &mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: &mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
			Resources:                  mdResources,
		},
	}
	g.Expect(c.Create(context.TODO(), md1)).NotTo(HaveOccurred())

	md2 := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      testModelName2,
			Namespace: testNamespace,
			Labels: map[string]string{
				legion.DomainModelId:      testModelId,
				legion.DomainModelVersion: testModelVersion2,
			},
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   &mdReplicas,
			LivenessProbeInitialDelay:  &mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: &mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
			Resources:                  mdResources,
		},
	}
	g.Expect(c.Create(context.TODO(), md2)).NotTo(HaveOccurred())

	return []*legionv1alpha1.ModelDeployment{md1, md2}
}

func createModelTrainings(g *GomegaWithT, c client.Client) []*legionv1alpha1.ModelTraining {
	md1 := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      testModelName1,
			Namespace: testNamespace,
			Labels: map[string]string{
				legion.DomainModelId:      testModelId,
				legion.DomainModelVersion: testModelVersion1,
			},
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}
	g.Expect(c.Create(context.TODO(), md1)).NotTo(HaveOccurred())

	md2 := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      testModelName2,
			Namespace: testNamespace,
			Labels: map[string]string{
				legion.DomainModelId:      testModelId,
				legion.DomainModelVersion: testModelVersion2,
			},
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}
	g.Expect(c.Create(context.TODO(), md2)).NotTo(HaveOccurred())

	return []*legionv1alpha1.ModelTraining{md1, md2}
}
