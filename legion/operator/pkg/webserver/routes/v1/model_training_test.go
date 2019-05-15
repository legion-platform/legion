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
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	. "github.com/onsi/gomega"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"testing"
)

const (
	mtName          = "test-mt"
	mtToolchainType = "python"
	mtEntrypoint    = "script.py"
	mtVCSName       = "legion-test"
	mtImage         = "image-test:123"
	mtReference     = "feat/123"
)

func TestGetMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mt := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}
	g.Expect(c.Create(context.TODO(), mt)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mt)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/training/%s", mtName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(Equal(MTResponse{Name: mt.Name, Spec: mt.Spec, Status: mt.Status}))
}

func TestGetMTNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/training/not-found", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestGetAllMTEmptyResult(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/training", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var mtResponse []MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &mtResponse)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(mtResponse).Should(HaveLen(0))
}

func TestGetAllMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/training", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(2))

	for _, mt := range result {
		g.Expect(mt.Name).To(Or(Equal(testModelName1), Equal(testModelName2)))
	}
}

func TestGetAllMTByModelID(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelId, testModelId)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(2))

	for _, mt := range result {
		g.Expect(mt.Name).To(Or(Equal(testModelName1), Equal(testModelName2)))
	}
}

func TestGetAllMTByModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, testModelVersion1)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(1))
	g.Expect(result[0].Name).To(Equal(testModelName1))
}

func TestGetAllMTByWrongModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, "wrong-version")

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MTResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(0))
}

func TestCreateMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mtEntity := &MTRequest{
		Name: mtName,
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}

	mt := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
	}
	defer c.Delete(context.TODO(), mt)

	mtEntityBody, err := json.Marshal(mtEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/training", bytes.NewReader(mtEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusCreated))
	g.Expect(result.Message).Should(ContainSubstring("was created"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: mtName, Namespace: testNamespace}, mt)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(mt.Spec).To(Equal(mtEntity.Spec))
}

func TestCreateDuplicateMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mtEntity := &MTRequest{
		Name: mtName,
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}

	mt := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}

	g.Expect(c.Create(context.TODO(), mt)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mt)

	mtEntityBody, err := json.Marshal(mtEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/training", bytes.NewReader(mtEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusConflict))
	g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func TestUpdateMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mt := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}
	g.Expect(c.Create(context.TODO(), mt)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mt)

	mtEntity := &MTRequest{
		Name: mtName,
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: "python",
			Entrypoint:    mtEntrypoint + "123",
			VCSName:       mtVCSName + "123",
			Image:         mtImage + "123",
			Reference:     mtReference + "123",
		},
	}

	mtEntityBody, err := json.Marshal(mtEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/training", bytes.NewReader(mtEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was updated"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: mtName, Namespace: testNamespace}, mt)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mt.Spec).To(Equal(mtEntity.Spec))
}

func TestUpdateMTNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	mtEntity := &MTRequest{
		Name: mtName,
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}

	mtEntityBody, err := json.Marshal(mtEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/training", bytes.NewReader(mtEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteMT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mt := &legionv1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mtName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelTrainingSpec{
			ToolchainType: mtToolchainType,
			Entrypoint:    mtEntrypoint,
			VCSName:       mtVCSName,
			Image:         mtImage,
			Reference:     mtReference,
		},
	}
	g.Expect(c.Create(context.TODO(), mt)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mt)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/training/%s", mtName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	var mtList legionv1alpha1.ModelTrainingList
	err = c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mtList)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mtList.Items).To(HaveLen(0))
}

func TestDeleteMTNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/training/%s", mtName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteAllMTEmptyResult(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, "/api/v1/model/training", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(And(
		ContainSubstring("Selector does not restrict"),
		ContainSubstring("Skip deletion"),
	))

	var mtList legionv1alpha1.ModelTrainingList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mtList)).ToNot(HaveOccurred())
	g.Expect(mtList.Items).To(HaveLen(2))
}

func TestDeleteAllMTByWrongModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, "wrong-version")

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(And(
		ContainSubstring("Not found"),
		ContainSubstring("Skip deletion"),
	))

	var mtList legionv1alpha1.ModelTrainingList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mtList)).ToNot(HaveOccurred())
	g.Expect(mtList.Items).To(HaveLen(2))
}

func TestDeleteAllMTByModelID(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelId, testModelId)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("Model training were removed"))

	var mtList legionv1alpha1.ModelTrainingList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mtList)).ToNot(HaveOccurred())
	g.Expect(mtList.Items).To(HaveLen(0))
}

func TestDeleteAllMTByModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mts := createModelTrainings(g, c)
	for _, mt := range mts {
		defer c.Delete(context.TODO(), mt)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, testModelVersion2)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/training?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("Model training were removed"))

	var mtList legionv1alpha1.ModelTrainingList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mtList)).ToNot(HaveOccurred())
	g.Expect(mtList.Items).To(HaveLen(1))
	g.Expect(mtList.Items[0].Name).To(Equal(testModelName1))
}
