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

package aggregator

import (
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/feedback"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

const (
	testFeedbackUrl = "/api/v1/feedback/model/stub-model-5-1/api/model"
)

// DataLoggingMock
type DataLoggingMock struct {
	mock.Mock
}

func (m *DataLoggingMock) Post(tag string, message interface{}) error {
	fmt.Println("Mocked DataLoggingMock Post function invoked")
	args := m.Called(tag, message)

	return args.Error(0)
}

func (m *DataLoggingMock) Close() error {
	return nil
}

func buildRouterWithDataMock() (*gin.Engine, *DataLoggingMock, string) {
	router := gin.Default()
	testTagName := "test-name"

	mockedDataLogger := new(DataLoggingMock)
	router.Use(DataLoggingMiddleware(mockedDataLogger, testTagName))
	attachRoutes(router)

	return router, mockedDataLogger, testTagName
}

func TestSendFeedbackWithoutHeader(t *testing.T) {
	router, _, _ := buildRouterWithDataMock()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", testFeedbackUrl, nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 400, w.Code)
	assert.Equal(t, "{\"error\":\"x-request-id header is missed\"}", w.Body.String())
}

func buildMessage(modelName, modelVersion, requestID string, payload map[string]interface{}) feedback.ModelFeedback {
	return feedback.ModelFeedback{
		ModelName:    modelName,
		ModelVersion: modelVersion,
		Payload:      payload,
		RequestID:    requestID,
	}
}

func ensureValidJSONResponse(t *testing.T, w *httptest.ResponseRecorder, expectedStructure interface{}) {
	assert.Equal(t, 200, w.Code)
	headers := w.Header()
	assert.Equal(t, "application/json; charset=utf-8", headers.Get("Content-Type"))

	var response FeedbackResponse
	assert.Nil(t, json.Unmarshal(w.Body.Bytes(), &response))
	assert.Equal(t, expectedStructure, response)
}

func TestSendFeedbackWithOnlyHeader(t *testing.T) {
	router, mocked, tag := buildRouterWithDataMock()
	modelName, modelVersion, requestID := "test-name", "1.0", "test-request-id"

	expectedPayload := map[string]interface{}{}
	expectedMessage := buildMessage(modelName, modelVersion, requestID, expectedPayload)

	mocked.On("Post", tag, expectedMessage).Return(nil)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", testFeedbackUrl, nil)
	req.Header.Set(feedback.RequestIdHeaderKey, requestID)
	req.Header.Set(feedback.ModelNameHeaderKey, modelName)
	req.Header.Set(feedback.ModelVersionHeaderKey, modelVersion)
	router.ServeHTTP(w, req)

	ensureValidJSONResponse(t, w, FeedbackResponse{Message: expectedMessage})
	mocked.AssertExpectations(t)
}

func TestIndexRoute(t *testing.T) {
	router, _, _ := buildRouterWithDataMock()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "{\"links\":[\"/api/v1/feedback/*any\"]}", w.Body.String())
}

func TestNotFoundRoute(t *testing.T) {
	router, _, _ := buildRouterWithDataMock()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/incorrect-route", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 404, w.Code)
	assert.Equal(t, "{\"error\":\"Incorrect URL\"}", w.Body.String())
}
