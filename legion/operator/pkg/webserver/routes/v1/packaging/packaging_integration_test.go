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

package packaging_test

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	. "github.com/onsi/gomega"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	piID           = "ti-test"
	piEntrypoint   = "test-entrypoint"
	piDefaultImage = "test:image"
	piPrivileged   = false
)

func TestGetPackagingIntegration(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c, _ := createEnvironment()

	pi := newPackagingIntegration()
	g.Expect(c.CreatePackagingIntegration(pi)).NotTo(HaveOccurred())
	defer c.DeletePackagingIntegration(pi.ID)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("/packaging/integration/%s", piID), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result packaging.PackagingIntegration
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Spec).Should(Equal(pi.Spec))
}

func TestGetPackagingIntegrationNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodGet, "/packaging/integration/not-found", nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestCreatePackagingIntegration(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c, _ := createEnvironment()

	piEntity := newPackagingIntegration()
	defer c.DeletePackagingIntegration(piID)

	piEntityBody, err := json.Marshal(piEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/packaging/integration", bytes.NewReader(piEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var piResponse packaging.PackagingIntegration
	err = json.Unmarshal(w.Body.Bytes(), &piResponse)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusCreated))
	g.Expect(piResponse.ID).Should(Equal(piEntity.ID))
	g.Expect(piResponse.Spec).Should(Equal(piEntity.Spec))

	pi, err := c.GetPackagingIntegration(piID)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(pi.Spec).To(Equal(piEntity.Spec))
}

func TestCreateDuplicatePackagingIntegration(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c, _ := createEnvironment()

	pi := newPackagingIntegration()
	g.Expect(c.CreatePackagingIntegration(pi)).NotTo(HaveOccurred())
	defer c.DeletePackagingIntegration(piID)

	piEntityBody, err := json.Marshal(pi)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/packaging/integration", bytes.NewReader(piEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusConflict))
	g.Expect(result.Message).Should(ContainSubstring("already exists"))
}

func TestUpdatePackagingIntegration(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c, _ := createEnvironment()

	pi := newPackagingIntegration()
	g.Expect(c.CreatePackagingIntegration(pi)).NotTo(HaveOccurred())
	defer c.DeletePackagingIntegration(pi.ID)

	piEntity := newPackagingIntegration()
	piEntity.Spec.Entrypoint = "new-entrypoint"

	piEntityBody, err := json.Marshal(piEntity)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/packaging/integration", bytes.NewReader(piEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var piResponse packaging.PackagingIntegration
	err = json.Unmarshal(w.Body.Bytes(), &piResponse)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(piResponse.ID).Should(Equal(piEntity.ID))
	g.Expect(piResponse.Spec).Should(Equal(piEntity.Spec))

	pi, err = c.GetPackagingIntegration(piID)
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(pi.Spec).To(Equal(piEntity.Spec))
}

func TestUpdatePackagingIntegrationNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _, _ := createEnvironment()

	pi := newPackagingIntegration()
	piEntityBody, err := json.Marshal(pi)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPut, "/packaging/integration", bytes.NewReader(piEntityBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}

func TestDeletePackagingIntegration(t *testing.T) {
	g := NewGomegaWithT(t)
	server, c, _ := createEnvironment()

	pi := newPackagingIntegration()
	g.Expect(c.CreatePackagingIntegration(pi)).NotTo(HaveOccurred())
	defer c.DeletePackagingIntegration(pi.ID)

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/packaging/integration/%s", piID), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusOK))
	g.Expect(result.Message).Should(ContainSubstring("was deleted"))

	piList, err := c.GetPackagingIntegrationList()
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(piList).To(HaveLen(0))
}

func TestDeletePackagingIntegrationNotFound(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _, _ := createEnvironment()

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("/packaging/integration/%s", piID), nil)
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result routes.HTTPResult
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).Should(Equal(http.StatusNotFound))
	g.Expect(result.Message).Should(ContainSubstring("not found"))
}
