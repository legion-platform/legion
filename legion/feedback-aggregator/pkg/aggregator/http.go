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
	"github.com/spf13/viper"
	"github.com/zsais/go-gin-prometheus"
	"log"

	"github.com/gin-gonic/gin"
)

const (
	feedbackUri = "/api/v1/feedback/*any"

	dataLoggingInstance = "dataLoggingInstance"
	dataLoggingTag      = "dataLoggingTag"

	CfgPort = "port"
)

type FeedbackResponse struct {
	Message feedback.ModelFeedback `json:"message"`
}

func attachRoutes(router *gin.Engine) {
	router.GET("/", handleIndex)
	router.POST(feedbackUri, handleFeedbackEndpoint)
	router.NoRoute(handleNoRoute)

	p := ginprometheus.NewPrometheus("gin")
	p.Use(router)
}

// DataLoggingMiddleware adds dataLoggingInstance and dataLoggingTag contexts to request
func DataLoggingMiddleware(instance feedback.DataLogging, loggerTag string) gin.HandlerFunc {
	return func(c *gin.Context) {
		log.Println("Setting middleware DataLogging")
		c.Set(dataLoggingInstance, instance)
		c.Set(dataLoggingTag, loggerTag)
		c.Next()
	}
}

// StartServer starts HTTP server
func StartServer(dataLogger feedback.DataLogging) (err error) {
	router := gin.Default()
	addr := fmt.Sprintf("0.0.0.0:%d", viper.GetInt(CfgPort))

	router.Use(DataLoggingMiddleware(dataLogger, viper.GetString(feedback.CfgFeedbackTag)))
	attachRoutes(router)

	log.Printf("Starting server on %s", addr)
	return router.Run(addr)
}
