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
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

const (
	testModelDeploymentName = "test-model-deployment-name"
)

func TestGenerateTokenWithoutExpirationDate(t *testing.T) {
	dir, _ := os.Getwd()
	fmt.Println(dir)
	viper.Set(legion.ModelJwtPrivateKey, "../../../../hack/tests/keys/private_key.pem")

	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	viper.Set(legion.JwtEnabled, true)

	tokenRequest := &TokenRequest{RoleName: testModelDeploymentName}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/token", bytes.NewReader(tokenRequestBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).To(Equal(http.StatusCreated))
	g.Expect(result.Token).ToNot(BeEmpty())
}

func TestDisabledJWT(t *testing.T) {
	g := NewGomegaWithT(t)
	server, _ := createEnvironment()

	viper.Set(legion.JwtEnabled, false)

	tokenRequest := &TokenRequest{RoleName: testModelDeploymentName}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	g.Expect(err).NotTo(HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/token", bytes.NewReader(tokenRequestBody))
	g.Expect(err).NotTo(HaveOccurred())
	server.ServeHTTP(w, req)

	var result TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(HaveOccurred())

	g.Expect(w.Code).To(Equal(http.StatusCreated))
	g.Expect(result.Token).To(BeEmpty())
}
