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
	"fmt"
	"log"
	"net/http"

	gin "github.com/gin-gonic/gin"
)

func handleIndex(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"links": []string{uriFormat}})
}

func handleFeedbackEndpoint(c *gin.Context) {
	modelID := c.Param("model_id")
	modelVersion := c.Param("model_version")

	if len(modelID) == 0 || len(modelVersion) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Incorrect model_id / model_version field value"})
		return
	}

	requestID := c.GetHeader(requestIDHeader)
	if len(requestID) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("%s header is missed", requestIDHeader)})
		return
	}

	message := map[string]interface{}{
		"payload":       ParseRequestDataset(c),
		"request_id":    requestID,
		"model_id":      modelID,
		"model_version": modelVersion,
	}

	logger := c.MustGet(dataLoggingInstance).(dataLogging)
	loggerTag := c.MustGet(dataLoggingTag).(string)

	err := logger.Post(loggerTag, message)

	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "Cannot deliver message"})
		log.Printf("Cannot deliver message: %s\n", err)
	} else {
		c.JSON(http.StatusOK, gin.H{"error": false, "registered": true, "message": message})
	}
}

func handleNoRoute(c *gin.Context) {
	c.JSON(http.StatusNotFound, gin.H{"error": "Incorrect URL"})
}
