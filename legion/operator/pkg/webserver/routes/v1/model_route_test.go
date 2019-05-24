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
	mrName = "test-mr"
	mrUrl  = "test/url"
)

func TestGetMR(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}
	g.Expect(c.Create(context.TODO(), mr)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/route/%s", mrName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result MRResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(Equal(MRResponse{Name: mr.Name, Spec: mr.Spec, Status: &mr.Status}))
}

func TestGetMRNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/route/not-found", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestCreateMR(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mrEntity := &MRRequest{
		Name: mrName,
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}

	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
	}
	defer c.Delete(context.TODO(), mr)

	mrEntityBody, err := json.Marshal(mrEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/route", bytes.NewReader(mrEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusCreated))
	g.Expect(result.Message).Should(ContainSubstring("was created"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: mrName, Namespace: testNamespace}, mr)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(mr.Spec).To(Equal(mrEntity.Spec))
}

func TestCreateDuplicateMR(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mrEntity := &MRRequest{
		Name: mrName,
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}

	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}

	g.Expect(c.Create(context.TODO(), mr)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	mrEntityBody, err := json.Marshal(mrEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/route", bytes.NewReader(mrEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusConflict))
	g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func TestUpdateMR(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{

			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}
	g.Expect(c.Create(context.TODO(), mr)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	newUrl := "/new/url"
	mrEntity := &MRRequest{
		Name: mrName,
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              newUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}

	mrEntityBody, err := json.Marshal(mrEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/route", bytes.NewReader(mrEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was updated"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: mrName, Namespace: testNamespace}, mr)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mr.Spec).To(Equal(mrEntity.Spec))
}

func TestUpdateMRNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	newUrl := "/new/url"
	mrEntity := &MRRequest{
		Name: mrName,
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              newUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}

	mrEntityBody, err := json.Marshal(mrEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/route", bytes.NewReader(mrEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteMR(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			UrlPrefix:              mrUrl,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{},
		},
	}
	g.Expect(c.Create(context.TODO(), mr)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/route/%s", mrName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	var mrList legionv1alpha1.ModelRouteList
	err = c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mrList)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mrList.Items).To(HaveLen(0))
}

func TestDeleteMRNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/route/%s", mrName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}
