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

package modeltraining

import (
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"testing"
	"time"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/onsi/gomega"
	"golang.org/x/net/context"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

const (
	timeout           = time.Second * 5
	namespace         = "default"
	modelTrainingName = "model-training-test"
	vcsName           = "test-vcs"
	vscCredential     = "bG9sCg=="
)

var (
	c               client.Client
	expectedRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      modelTrainingName,
			Namespace: namespace,
		},
	}
	vcs = &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: namespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             "git",
			Uri:              "git@github.com:legion-platform/legion.git",
			DefaultReference: "refs/heads/master",
			Credential:       vscCredential,
		},
	}
	vscSecret = &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: namespace,
		},
		Data: map[string][]byte{
			utils.GitSSHKeyFileName: []byte(vscCredential),
		},
	}
)

func generateConfig() legion.OperatorConfig {
	return legion.OperatorConfig{
		BuilderImage:           "builder_image_from_config",
		MetricHost:             "metric_host_from_config",
		MetricPort:             "metric_port_from_config",
		MetricEnabled:          "metric_enabled_from_config",
		PythonToolchainImage:   "python_toolchain_image_from_config",
		BuildImagePrefix:       "build_image_prefix_from_config",
		DockerRegistry:         "docker_registry_from_config",
		DockerRegistryUser:     "docker_registry_user_from_config",
		DockerRegistryPassword: "docker_registry_password_from_config",
	}
}

func TestBasicReconcile(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(gomega.HaveOccurred())
	c = mgr.GetClient()

	recFn, requests := SetupTestReconcile(newReconciler(mgr))
	g.Expect(add(mgr, recFn)).NotTo(gomega.HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)
	legion.OperatorConf = generateConfig()

	defer func() {
		close(stopMgr)
		mgrStopped.Wait()
	}()

	g.Expect(c.Create(context.TODO(), vcs)).NotTo(gomega.HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	g.Expect(c.Create(context.TODO(), vscSecret)).NotTo(gomega.HaveOccurred())
	defer c.Delete(context.TODO(), vscSecret)

	modelTraining := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      modelTrainingName,
			Namespace: namespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: "python",
			VCSName:       vcsName,
			Entrypoint:  "some entrypoint",
		},
	}

	g.Expect(c.Create(context.TODO(), modelTraining)).NotTo(gomega.HaveOccurred())
	defer c.Delete(context.TODO(), modelTraining)

	g.Eventually(requests, timeout).Should(gomega.Receive(gomega.Equal(expectedRequest)))
	// Skip event of pod creation
	g.Eventually(requests, timeout).Should(gomega.Receive(gomega.Equal(expectedRequest)))

	pod := &corev1.Pod{}
	g.Expect(c.Get(context.TODO(),
		types.NamespacedName{
			Name:      legion.GenerateBuildModelName(modelTrainingName),
			Namespace: namespace,
		}, pod),
	).NotTo(gomega.HaveOccurred())

	g.Expect(len(pod.Spec.Containers)).To(gomega.Equal(2))
}
