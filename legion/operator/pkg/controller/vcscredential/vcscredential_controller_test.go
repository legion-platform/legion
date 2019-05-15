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

package vcscredential

import (
	"encoding/base64"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"testing"
	"time"

	. "github.com/onsi/gomega"
	"golang.org/x/net/context"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

const (
	timeout             = time.Second * 5
	vcsName             = "test-vcs"
	vcsNamespace        = "default"
	vscDefaultReference = "refs/heads/master"
	vscUri              = "git@github.com:legion-platform/legion.git"
	vscType             = "git"
	vcsPublicKey        = "hardcodedKey"
)

var (
	c               client.Client
	expectedRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name: vcsName, Namespace: vcsNamespace,
		},
	}
)

func mocKeyEvaluator(image string) (string, error) {
	return vcsPublicKey, nil
}

func checkSecret(g *GomegaWithT, creds string) {
	secret := &corev1.Secret{}
	err := c.Get(context.TODO(),
		types.NamespacedName{
			Name:      legion.GenerateVcsSecretName(vcsName),
			Namespace: vcsNamespace,
		},
		secret,
	)
	g.Expect(err).NotTo(HaveOccurred())

	expectedIdRsa, err := base64.StdEncoding.DecodeString(creds)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(string(secret.Data[utils.GitSSHKeyFileName])).Should(BeIdenticalTo(string(expectedIdRsa)))

	g.Expect(string(secret.Data[utils.PublicSshKeyName])).To(Equal(vcsPublicKey))
}

func TestBasicReconcile(t *testing.T) {
	g := NewGomegaWithT(t)

	creds := "bG9sCg=="
	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: vcsNamespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}

	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(HaveOccurred())
	c = mgr.GetClient()

	recFn, requests := SetupTestReconcile(newConfigurableReconciler(mgr, mocKeyEvaluator))
	g.Expect(add(mgr, recFn)).NotTo(HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)

	defer func() {
		close(stopMgr)
		mgrStopped.Wait()
	}()

	g.Expect(c.Create(context.TODO(), vcs)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))
	// Skip event of secret creation
	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))
	checkSecret(g, creds)

	// Try to update vcs credentials and check secret state
	newCreds := "a2VrCg=="
	vcs.Spec.Credential = newCreds

	g.Expect(c.Update(context.TODO(), vcs)).NotTo(HaveOccurred())

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))
	checkSecret(g, newCreds)
}
