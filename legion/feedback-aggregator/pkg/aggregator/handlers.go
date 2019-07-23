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
	"fmt"
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/feedback"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"

	"github.com/gin-gonic/gin"
)

var logH = logf.Log.WithName("aggregator-handlers")

func handleIndex(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"links": []string{feedbackUri}})
}

func handleFeedbackEndpoint(c *gin.Context) {
	modelName := c.GetHeader(feedback.ModelNameHeaderKey)
	modelVersion := c.GetHeader(feedback.ModelVersionHeaderKey)

	message := feedback.ModelFeedback{
		ModelName:    modelName,
		ModelVersion: modelVersion,
	}

	message.RequestID = c.GetHeader(feedback.LegionRequestIdHeaderKey)
	if len(message.RequestID) == 0 {
		message.RequestID = c.GetHeader(feedback.RequestIdHeaderKey)
		if len(message.RequestID) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("%s header is missed", feedback.RequestIdHeaderKey)})
			return
		}
	}

	if len(modelName) == 0 || len(modelVersion) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": fmt.Sprintf("%s or %s header is empty",
				feedback.ModelNameHeaderKey, feedback.ModelVersionHeaderKey),
		})
		return
	}

	payload, err := ParseRequestDataset(c)
	if err != nil {
		logH.Error(err, "Parsing failed")

		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot parse data"})
		return
	}

	message.Payload = payload

	logger := c.MustGet(dataLoggingInstance).(feedback.DataLogging)
	loggerTag := c.MustGet(dataLoggingTag).(string)

	err = logger.Post(loggerTag, message)

	if err != nil {
		logH.Error(err, "Cannot deliver message")

		c.JSON(http.StatusBadGateway, gin.H{"error": "Cannot deliver message"})
	} else {
		collectedFeedback.Add(1)
		c.JSON(http.StatusOK, FeedbackResponse{Message: message})
	}
}

func handleNoRoute(c *gin.Context) {
	c.JSON(http.StatusNotFound, gin.H{"error": "Incorrect URL"})
}
