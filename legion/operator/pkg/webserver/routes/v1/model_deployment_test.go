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
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"testing"
)

const (
	mdName                  = "test-model-deployment"
	mdImage                 = "test/test:123"
	mdReplicas              = int32(2)
	mdLivenessInitialDelay  = int32(60)
	mdReadinessInitialDelay = int32(30)
)

var (
	mdAnnotations = map[string]string{"k1": "v1", "k2": "v2"}
	mdResources   = &corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("222m"),
			"memory": resource.MustParse("222Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("111m"),
			"memory": resource.MustParse("111Mi"),
		},
	}
)

func TestGetMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
			Resources:                  mdResources,
		},
	}
	g.Expect(c.Create(context.TODO(), md)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/deployment/%s", mdName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(Equal(MDResponse{Name: md.Name, Spec: md.Spec, Status: &legionv1alpha1.ModelDeploymentStatus{}}))
}

func TestGetMDNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/deployment/not-found", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestGetAllMDEmptyResult(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/deployment", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var mdResponse []MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &mdResponse)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(mdResponse).Should(HaveLen(0))
}

func TestGetAllMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/api/v1/model/deployment", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(2))

	for _, md := range result {
		g.Expect(md.Name).To(Or(Equal(testModelName1), Equal(testModelName2)))
	}
}

func TestGetAllMDByModelID(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelId, testModelId)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(2))

	for _, md := range result {
		g.Expect(md.Name).To(Or(Equal(testModelName1), Equal(testModelName2)))
	}
}

func TestGetAllMDByModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, testModelVersion1)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(1))
	g.Expect(result[0].Name).To(Equal(testModelName1))
}

func TestGetAllMDByWrongModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, "wrong-version")

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result []MDResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result).Should(HaveLen(0))
}

func TestCreateMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mdEntity := &MDResponse{
		Name: mdName,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
	}
	defer c.Delete(context.TODO(), md)

	mdEntityBody, err := json.Marshal(mdEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/deployment", bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusCreated))
	g.Expect(result.Message).Should(ContainSubstring("was created"))

	err = c.Get(context.TODO(), types.NamespacedName{Name: mdName, Namespace: testNamespace}, md)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(md.Spec).To(Equal(mdEntity.Spec))
}

func TestCreateDuplicateMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mdEntity := &MDResponse{
		Name: mdName,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}

	g.Expect(c.Create(context.TODO(), md)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	mdEntityBody, err := json.Marshal(mdEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/deployment", bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusConflict))
	g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func TestUpdateMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}
	g.Expect(c.Create(context.TODO(), md)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	mdEntity := &MDRequest{
		Name: mdName,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      "new-image:123",
			Replicas:                   mdReplicas + 1,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay + 1,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay + 1,
			Annotations:                nil,
		},
	}

	mdEntityBody, err := json.Marshal(mdEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/deployment", bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was updated"))

	md = &legionv1alpha1.ModelDeployment{}
	err = c.Get(context.TODO(), types.NamespacedName{Name: mdName, Namespace: testNamespace}, md)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mdEntity.Spec).To(Equal(md.Spec))
}

func TestUpdateMDNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	mdEntity := &MDResponse{
		Name: mdName,
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      "new-image:123",
			Replicas:                   mdReplicas + 1,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay + 1,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay + 1,
		},
	}

	mdEntityBody, err := json.Marshal(mdEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/api/v1/model/deployment", bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestScaleMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	newReplicasNumber := mdReplicas + 1

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}
	g.Expect(c.Create(context.TODO(), md)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	replicasEntity := &MDReplicas{Replicas: newReplicasNumber}

	mdEntityBody, err := json.Marshal(replicasEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, fmt.Sprintf("/api/v1/model/deployment/%s/scale", mdName),
		bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(http.StatusOK).To(Equal(w.Code))
	g.Expect(result.Message).To(ContainSubstring("was updated"))

	md = &legionv1alpha1.ModelDeployment{}
	err = c.Get(context.TODO(), types.NamespacedName{Name: mdName, Namespace: testNamespace}, md)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(newReplicasNumber).To(Equal(md.Spec.Replicas))
}

func TestScaleMDNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	mdReplicas := &MDReplicas{Replicas: 3}

	mdEntityBody, err := json.Marshal(mdReplicas)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, fmt.Sprintf("/api/v1/model/deployment/%s/scale", "notfound"),
		bytes.NewReader(mdEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteMD(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mdName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   mdReplicas,
			LivenessProbeInitialDelay:  mdLivenessInitialDelay,
			ReadinessProbeInitialDelay: mdReadinessInitialDelay,
			Annotations:                mdAnnotations,
		},
	}
	g.Expect(c.Create(context.TODO(), md)).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/deployment/%s", mdName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	var mdList legionv1alpha1.ModelDeploymentList
	err = c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mdList)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(mdList.Items).To(HaveLen(0))
}

func TestDeleteMDNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()
	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/deployment/%s", mdName), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeleteAllMDEmptyResult(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, "/api/v1/model/deployment", nil)
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

	var mdList legionv1alpha1.ModelDeploymentList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mdList)).ToNot(HaveOccurred())
	g.Expect(mdList.Items).To(HaveLen(2))
}

func TestDeleteAllMDByWrongModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, "wrong-version")

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
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

	var mdList legionv1alpha1.ModelDeploymentList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mdList)).ToNot(HaveOccurred())
	g.Expect(mdList.Items).To(HaveLen(2))
}

func TestDeleteAllMDByModelID(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelId, testModelId)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("Model deployment were removed"))

	var mdList legionv1alpha1.ModelDeploymentList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mdList)).ToNot(HaveOccurred())
	g.Expect(mdList.Items).To(HaveLen(0))
}

func TestDeleteAllMDByModelVersion(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c := createEnvironment()

	mds := createModelDeployments(g, c)
	for _, md := range mds {
		defer c.Delete(context.TODO(), md)
	}

	params := url.Values{}
	params.Add(legion.DomainModelVersion, testModelVersion2)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/api/v1/model/deployment?%s", params.Encode()), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("Model deployment were removed"))

	var mdList legionv1alpha1.ModelDeploymentList
	g.Expect(c.List(context.TODO(), &client.ListOptions{Namespace: testNamespace}, &mdList)).ToNot(HaveOccurred())
	g.Expect(mdList.Items).To(HaveLen(1))
	g.Expect(mdList.Items[0].Name).To(Equal(testModelName1))
}
