/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package http_test

import (
	"encoding/json"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packaging_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	packaging_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging/http"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	piID = "test-pi-id"
)

var (
	pi = &packaging.PackagingIntegration{
		ID: piID,
		Spec: packaging.PackagingIntegrationSpec{
			Entrypoint:   "/test/entrypoint",
			DefaultImage: "default:image",
		},
	}
)

type piSuite struct {
	suite.Suite
	g            *GomegaWithT
	ts           *httptest.Server
	piHTTPClient packaging_repository.Repository
}

func (s *piSuite) SetupSuite() {
	s.ts = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/v1/packaging/integration/test-pi-id":
			if r.Method == http.MethodGet {
				w.WriteHeader(http.StatusOK)
				piBytes, err := json.Marshal(pi)
				if err != nil {
					// Must not be occurred
					panic(err)
				}

				_, err = w.Write(piBytes)
				if err != nil {
					// Must not be occurred
					panic(err)
				}
			} else {
				NotFound(w, r)
			}
		default:
			NotFound(w, r)
		}
	}))

	s.piHTTPClient = packaging_http_repository.NewRepository(s.ts.URL, "")
}

func (s *piSuite) TearDownSuite() {
	s.ts.Close()
}

func (s *piSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestSuite(t *testing.T) {
	suite.Run(t, new(piSuite))
}

func (s *piSuite) TestPackagingIntegrationGet() {
	piResult, err := s.piHTTPClient.GetPackagingIntegration(piID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(pi).Should(Equal(piResult))
}

func (s *piSuite) TestPackagingoIntegrationNotFound() {
	_, err := s.piHTTPClient.GetPackagingIntegration("pi-not-found")
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}
