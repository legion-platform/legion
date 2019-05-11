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

package utils

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	gin "github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
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
	req, _ := http.NewRequest("POST", "/api/model/abc/1.0/feedback", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 400, w.Code)
	assert.Equal(t, "{\"error\":\"Request-ID header is missed\"}", w.Body.String())
}

func buildFeedbackURL(modelID, modelVersion string) string {
	return fmt.Sprintf("/api/model/%s/%s/feedback", modelID, modelVersion)
}

func buildMessage(modelID, modelVersion, requestID string, payload map[string]interface{}) map[string]interface{} {
	return map[string]interface{}{
		"model_id":      modelID,
		"model_version": modelVersion,
		"payload":       payload,
		"request_id":    requestID,
	}
}

func buildExpectedResponse(message map[string]interface{}) map[string]interface{} {
	return map[string]interface{}{
		"message":    message,
		"error":      false,
		"registered": true,
	}
}

func ensureValidJSONResponse(t *testing.T, w *httptest.ResponseRecorder, expectedStructure interface{}) {
	assert.Equal(t, 200, w.Code)
	headers := w.Header()
	assert.Equal(t, "application/json; charset=utf-8", headers.Get("Content-Type"))
	var response interface{}
	assert.Nil(t, json.Unmarshal(w.Body.Bytes(), &response))
	assert.Equal(t, expectedStructure, response)
}

func TestSendFeedbackWithOnlyHeader(t *testing.T) {
	router, mocked, tag := buildRouterWithDataMock()
	modelID, modelVersion, requestID := "test-id", "1.0", "test-request-id"

	expectedPayload := map[string]interface{}{}
	expectedMessage := buildMessage(modelID, modelVersion, requestID, expectedPayload)
	expectedResponse := buildExpectedResponse(expectedMessage)

	mocked.On("Post", tag, expectedMessage).Return(nil)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", buildFeedbackURL(modelID, modelVersion), nil)
	req.Header.Set("Request-ID", requestID)
	router.ServeHTTP(w, req)

	ensureValidJSONResponse(t, w, expectedResponse)
	mocked.AssertExpectations(t)
}

func TestIndexRoute(t *testing.T) {
	router, _, _ := buildRouterWithDataMock()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "{\"links\":[\"/api/model/:model_id/:model_version/feedback\"]}", w.Body.String())
}

func TestNotFoundRoute(t *testing.T) {
	router, _, _ := buildRouterWithDataMock()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/incorrect-route", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 404, w.Code)
	assert.Equal(t, "{\"error\":\"Incorrect URL\"}", w.Body.String())
}
