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
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	. "github.com/onsi/gomega"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"net/http"
	"net/http/httptest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"testing"
)

const (
	vcsName             = "testvcs"
	vscDefaultReference = "refs/heads/master"
	vscUri              = "git@github.com:legion-platform/legion.git"
	vscType             = "git"
	creds               = "bG9sCg=="
)

func TestGetVCS(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}
	g.Expect(c.Create(context.TODO(), vcs)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/vcs/%s", vcsName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result VCSEntity
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(Equal(VCSEntity{Name: vcs.Name, Spec: vcs.Spec}))
}

func TestGetVCSNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/vcs/not-found", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestCreateVCS(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	vcsEntity := &VCSEntity{
		Name: vcsName,
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}

	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
	}
	defer c.Delete(context.TODO(), vcs)

	vcsEntityBody, err := json.Marshal(vcsEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/vcs", bytes.NewReader(vcsEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusCreated))
	g.Expect(result.Message).Should(ContainSubstring("was created"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: vcsName, Namespace: testNamespace}, vcs)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(vcs.Spec).To(Equal(vcsEntity.Spec))
}

func TestCreateDuplicateVCS(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	vcsEntity := &VCSEntity{
		Name: vcsName,
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}

	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}

	g.Expect(c.Create(context.TODO(), vcs)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	vcsEntityBody, err := json.Marshal(vcsEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/vcs", bytes.NewReader(vcsEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusConflict))
	g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func TestUpdateVCS(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}
	g.Expect(c.Create(context.TODO(), vcs)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	vcsEntity := &VCSEntity{
		Name: vcsName,
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              "new-url",
			DefaultReference: "new-default-reference",
			Credential:       "new-creds",
		},
	}

	vcsEntityBody, err := json.Marshal(vcsEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/vcs", bytes.NewReader(vcsEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was updated"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: vcsName, Namespace: testNamespace}, vcs)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(vcs.Spec).To(Equal(vcsEntity.Spec))
}

func TestUpdateVCSNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	vcsEntity := &VCSEntity{
		Name: vcsName,
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              "new-url",
			DefaultReference: "new-default-reference",
			Credential:       "new-creds",
		},
	}

	vcsEntityBody, err := json.Marshal(vcsEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/vcs", bytes.NewReader(vcsEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteVCS(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	vcs := &legionv1alpha1.VCSCredential{
		ObjectMeta: metav1.ObjectMeta{
			Name:      vcsName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.VCSCredentialSpec{
			Type:             vscType,
			Uri:              vscUri,
			DefaultReference: vscDefaultReference,
			Credential:       creds,
		},
	}
	g.Expect(c.Create(context.TODO(), vcs)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), vcs)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/vcs/%s", vcsName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	var vcsList legionv1alpha1.VCSCredentialList
	err = c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &vcsList)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(vcsList.Items).To(HaveLen(0))
}

func TestDeleteVCSNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/vcs/%s", vcsName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}
