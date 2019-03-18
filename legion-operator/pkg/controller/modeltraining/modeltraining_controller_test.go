/*

   Copyright 2019 EPAM Systems

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

*/

package modeltraining

import (
	"testing"
	"time"

	legionv1alpha1 "github.com/legion-platform/legion/legion-operator/pkg/apis/legion/v1alpha1"
	"github.com/onsi/gomega"
	"golang.org/x/net/context"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

var c client.Client

const (
	timeout          = time.Second * 5
	baseInstanceName = "test-instance"
	vcsInstanceName  = "test-vcs"
	namespace        = "default"
)

var (
	podKey            = types.NamespacedName{Name: baseInstanceName + "-training-pod", Namespace: namespace}
	secretKey         = types.NamespacedName{Name: baseInstanceName + "-training-secret", Namespace: namespace}
	expectedMtRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{Name: baseInstanceName, Namespace: namespace},
	}
	expectedVcsRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{Name: vcsInstanceName, Namespace: namespace},
	}
	expectedPodRequest = reconcile.Request{
		NamespacedName: podKey,
	}
	expectedSecretRequest = reconcile.Request{
		NamespacedName: secretKey,
	}
)

func TestReconcile(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	// Instances for testing purposes
	mtInstance := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      baseInstanceName,
			Namespace: namespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: "python",
			VCSName:       vcsInstanceName,
			Entrypoint:    "run.py",
		},
	}

	vcsInstance := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsInstanceName,
			Namespace: namespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			VCSType:  "git",
			VCSUri:   "https://github.com/legion-platform/legion.git",
			VCSCreds: "test-creds-data",
		},
	}

	// Setup the Manager and Controller.  Wrap the Controller Reconcile function so it writes each request to a
	// channel when it is finished.
	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(gomega.HaveOccurred())
	c = mgr.GetClient()

	recFn, requests := SetupTestReconcile(newReconciler(mgr))
	g.Expect(add(mgr, recFn)).NotTo(gomega.HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)

	defer func() {
		close(stopMgr)
		mgrStopped.Wait()
	}()

	// Create the VCSCredential instance
	err = c.Create(context.TODO(), vcsInstance)
	g.Expect(err).NotTo(gomega.HaveOccurred())
	defer c.Delete(context.TODO(), vcsInstance)

	// Create the ModelTraining object
	err = c.Create(context.TODO(), mtInstance)
	g.Expect(err).NotTo(gomega.HaveOccurred())
	defer c.Delete(context.TODO(), mtInstance)

	// Check recieving of creation events
	g.Eventually(requests, timeout).Should(gomega.Receive(gomega.Equal(expectedMtRequest)))
	//g.Eventually(requests, timeout).Should(gomega.Receive(gomega.Equal(expectedVcsRequest)))

	// Find children
	pod := &corev1.Pod{}
	g.Eventually(func() error { return c.Get(context.TODO(), podKey, pod) }, timeout).
		Should(gomega.Succeed())

	secret := &corev1.Secret{} //+safeToCommit
	g.Eventually(func() error { return c.Get(context.TODO(), secretKey, secret) }, timeout).
		Should(gomega.Succeed())

	// Delete the Pod and expect Reconcile to be called for Pod recreation
	g.Expect(c.Delete(context.TODO(), pod)).NotTo(gomega.HaveOccurred())
	g.Eventually(requests, timeout).Should(gomega.Receive(gomega.Equal(expectedMtRequest)))

	// Check that pod has been recreated
	g.Eventually(func() error { return c.Get(context.TODO(), podKey, pod) }, timeout).
		Should(gomega.Succeed())

	// Check that children resources removes
	g.Eventually(func() error { return c.Delete(context.TODO(), pod) }, timeout).
		Should(gomega.MatchError("pods \"test-instance-training-pod\" not found"))

	g.Eventually(func() error { return c.Delete(context.TODO(), secret) }, timeout).
		Should(gomega.MatchError("secrets \"test-instance-training-secret\" not found"))

}
