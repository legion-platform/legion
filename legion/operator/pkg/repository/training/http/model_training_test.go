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
	"fmt"
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
	mtID = "test-mt-id"
)

var (
	mt = &training.ModelTraining{
		ID: mtID,
		Spec: v1alpha1.ModelTrainingSpec{
			Model: v1alpha1.ModelIdentity{
				Name:                 "model-name",
				Version:              "model-version",
				ArtifactNameTemplate: "",
			},
			Toolchain: "mlflow",
		},
	}
)

type mtSuite struct {
	suite.Suite
	g            *GomegaWithT
	ts           *httptest.Server
	mtHTTPClient training_repository.Repository
}

func NotFound(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotFound)
	_, err := fmt.Fprintf(w, "%s url not found", r.URL.Path)
	if err != nil {
		// Must not be occurred
		panic(err)
	}
}

func (s *mtSuite) SetupSuite() {
	s.ts = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/v1/model/training/test-mt-id":
			if r.Method != http.MethodGet {
				NotFound(w, r)
				return
			}

			w.WriteHeader(http.StatusOK)
			mtBytes, err := json.Marshal(mt)
			if err != nil {
				// Must not be occurred
				panic(err)
			}

			_, err = w.Write(mtBytes)
			if err != nil {
				// Must not be occurred
				panic(err)
			}
		default:
			NotFound(w, r)
		}
	}))

	s.mtHTTPClient = training_http_repository.NewRepository(s.ts.URL, "")
}

func (s *mtSuite) TearDownSuite() {
	s.ts.Close()
}

func (s *mtSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestMtSuite(t *testing.T) {
	suite.Run(t, new(mtSuite))
}

func (s *mtSuite) TestModelTrainingGet() {
	mtResult, err := s.mtHTTPClient.GetModelTraining(mtID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mt).Should(Equal(mtResult))
}

func (s *mtSuite) TestModelTrainingNotFound() {
	_, err := s.mtHTTPClient.GetModelTraining("mt-not-found")
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}
