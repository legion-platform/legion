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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	training_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	training_http_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training/http"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/suite"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	tiID = "test-ti-id"
)

var (
	ti = &training.ToolchainIntegration{
		ID: tiID,
		Spec: v1alpha1.ToolchainIntegrationSpec{
			Entrypoint:   "/test/entrypoint",
			DefaultImage: "default:image",
		},
	}
)

type tiSuite struct {
	suite.Suite
	g            *GomegaWithT
	ts           *httptest.Server
	tiHTTPClient training_repository.Repository
}

func (s *tiSuite) SetupSuite() {
	s.ts = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/v1/toolchain/integration/test-ti-id":
			if r.Method == http.MethodGet {
				w.WriteHeader(http.StatusOK)
				tiBytes, err := json.Marshal(ti)
				if err != nil {
					// Must not be occurred
					panic(err)
				}

				_, err = w.Write(tiBytes)
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

	s.tiHTTPClient = training_http_repository.NewRepository(s.ts.URL, "")
}

func (s *tiSuite) TearDownSuite() {
	s.ts.Close()
}

func (s *tiSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestSuite(t *testing.T) {
	suite.Run(t, new(tiSuite))
}

func (s *tiSuite) TestToolchainIntegrationGet() {
	tiResult, err := s.tiHTTPClient.GetToolchainIntegration(tiID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(ti).Should(Equal(tiResult))
}

func (s *tiSuite) TestToolchainIntegrationNotFound() {
	_, err := s.tiHTTPClient.GetToolchainIntegration("ti-not-found")
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}
