package v1

import (
	"bytes"
	"encoding/json"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/onsi/gomega"
	"github.com/spf13/viper"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	testModelID      = "test-model-id"
	testModelVersion = "test-model-version"
)

func TestGenerateTokenWithoutExpirationDate(t *testing.T) {
	g := gomega.NewGomegaWithT(t)
	server, _ := createEnvironment()

	viper.Set(legion.JwtSecret, "some-secret")

	tokenRequest := &TokenRequest{ModelID: testModelID, ModelVersion: testModelVersion}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	g.Expect(err).NotTo(gomega.HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/token", bytes.NewReader(tokenRequestBody))
	g.Expect(err).NotTo(gomega.HaveOccurred())
	server.ServeHTTP(w, req)

	var result TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(gomega.HaveOccurred())

	g.Expect(w.Code).To(gomega.Equal(http.StatusCreated))
	g.Expect(result.Token).ToNot(gomega.BeEmpty())
}

func TestDisabledJWT(t *testing.T) {
	g := gomega.NewGomegaWithT(t)
	server, _ := createEnvironment()

	viper.Set(legion.JwtSecret, "")

	tokenRequest := &TokenRequest{ModelID: testModelID, ModelVersion: testModelVersion}
	tokenRequestBody, err := json.Marshal(tokenRequest)
	g.Expect(err).NotTo(gomega.HaveOccurred())

	w := httptest.NewRecorder()
	req, err := http.NewRequest(http.MethodPost, "/api/v1/model/token", bytes.NewReader(tokenRequestBody))
	g.Expect(err).NotTo(gomega.HaveOccurred())
	server.ServeHTTP(w, req)

	var result TokenResponse
	err = json.Unmarshal(w.Body.Bytes(), &result)
	g.Expect(err).NotTo(gomega.HaveOccurred())

	g.Expect(w.Code).To(gomega.Equal(http.StatusCreated))
	g.Expect(result.Token).To(gomega.BeEmpty())
}
