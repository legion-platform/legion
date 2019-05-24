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
	"testing"

	. "github.com/onsi/gomega"
	"golang.org/x/net/context"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
)

const (
	vcsName                    = "test-vcs"
	vscDefaultReference        = "refs/heads/master"
	vscUri                     = "git@github.com:legion-platform/legion.git"
	vscType                    = "git"
	vscCreds                   = "bG9sCg=="
	vscNewCreds                = "a2VrCg=="
	notValidBase64             = "not valid base64"
	notValidBase64ErrorMessage = "illegal base64 data"
)

func TestStorageVCSCredential(t *testing.T) {
	g := NewGomegaWithT(t)

	key := types.NamespacedName{
		Name:      vcsName,
		Namespace: testNamespace,
	}
	created := &VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
		Spec: VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       vscCreds,
		},
	}

	g.Expect(created.DeepCopy().ValidatesAndSetDefaults()).NotTo(HaveOccurred())
	g.Expect(c.Create(context.TODO(), created)).NotTo(HaveOccurred())

	fetched := &VCSCredential{}
	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(created))

	updated := fetched.DeepCopy()
	updated.Spec.Credential = vscNewCreds
	g.Expect(c.Update(context.TODO(), updated)).NotTo(HaveOccurred())

	g.Expect(c.Get(context.TODO(), key, fetched)).NotTo(HaveOccurred())
	g.Expect(fetched).To(Equal(updated))
	g.Expect(fetched.Spec.Credential).To(Equal(vscNewCreds))

	g.Expect(c.Delete(context.TODO(), fetched)).NotTo(HaveOccurred())
	g.Expect(c.Get(context.TODO(), key, fetched)).To(HaveOccurred())
}

func TestValidateCredentials(t *testing.T) {
	g := NewGomegaWithT(t)

	vcs := VCSCredential{
		Spec: VCSCredentialSpec{
			Credential: notValidBase64,
		},
	}

	err := vcs.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(notValidBase64ErrorMessage))
}

func TestValidatePublicKey(t *testing.T) {
	g := NewGomegaWithT(t)

	vcs := VCSCredential{
		Spec: VCSCredentialSpec{
			PublicKey: notValidBase64,
		},
	}

	err := vcs.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(notValidBase64ErrorMessage))
}

func TestValidateUri(t *testing.T) {
	g := NewGomegaWithT(t)

	vcs := VCSCredential{
		Spec: VCSCredentialSpec{
			Uri: "",
		},
	}

	err := vcs.ValidatesAndSetDefaults()
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(emptyUriErrorMessage))
}
