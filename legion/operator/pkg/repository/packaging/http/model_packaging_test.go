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
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
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
	mpID = "test-mp-id"
)

var (
	mp = &packaging.ModelPackaging{
		ID: mpID,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName: "some-trained-art.zip",
			Image:        "some:image",
		},
	}
)

type mpSuite struct {
	suite.Suite
	g            *GomegaWithT
	ts           *httptest.Server
	mpHTTPClient packaging_repository.Repository
}

func NotFound(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotFound)
	_, err := fmt.Fprintf(w, "%s url not found", r.URL.Path)
	if err != nil {
		// Must not be occurred
		panic(err)
	}
}

func (s *mpSuite) SetupSuite() {
	s.ts = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/v1/model/packaging/test-mp-id":
			if r.Method != http.MethodGet {
				NotFound(w, r)
				return
			}

			w.WriteHeader(http.StatusOK)
			mpBytes, err := json.Marshal(mp)
			if err != nil {
				// Must not be occurred
				panic(err)
			}

			_, err = w.Write(mpBytes)
			if err != nil {
				// Must not be occurred
				panic(err)
			}
		case "/api/v1/model/packaging/test-mp-id/result":
			if r.Method != http.MethodPut {
				NotFound(w, r)
				return
			}

			w.WriteHeader(http.StatusOK)
			mpBytes, err := json.Marshal([]legionv1alpha1.ModelPackagingResult{})
			if err != nil {
				// Must not be occurred
				panic(err)
			}

			_, err = w.Write(mpBytes)
			if err != nil {
				// Must not be occurred
				panic(err)
			}
		default:
			NotFound(w, r)
		}
	}))

	s.mpHTTPClient = packaging_http_repository.NewRepository(s.ts.URL, "")
}

func (s *mpSuite) TearDownSuite() {
	s.ts.Close()
}

func (s *mpSuite) SetupTest() {
	s.g = NewGomegaWithT(s.T())
}

func TestMpSuite(t *testing.T) {
	suite.Run(t, new(mpSuite))
}

func (s *mpSuite) TestModelPackagingGet() {
	mpResult, err := s.mpHTTPClient.GetModelPackaging(mpID)
	s.g.Expect(err).ShouldNot(HaveOccurred())
	s.g.Expect(mp).Should(Equal(mpResult))
}

func (s *mpSuite) TestModelPackagingNotFound() {
	_, err := s.mpHTTPClient.GetModelPackaging("mp-not-found")
	s.g.Expect(err).Should(HaveOccurred())
	s.g.Expect(err.Error()).Should(ContainSubstring("not found"))
}

func (s *mpSuite) TestModelPackagingResultSaving() {
	err := s.mpHTTPClient.SaveModelPackagingResult(
		mpID,
		[]legionv1alpha1.ModelPackagingResult{{
			Name:  "test-name-1",
			Value: "test-value-1",
		}},
	)
	s.g.Expect(err).ShouldNot(HaveOccurred())
}
