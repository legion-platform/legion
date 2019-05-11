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
	"log"

	"github.com/fluent/fluent-logger-golang/fluent"
	gin "github.com/gin-gonic/gin"
)

const uriFormat = "/api/model/:model_id/:model_version/feedback"
const requestIDHeader = "Request-ID"
const maxRetryToDeliver = 5
const dataLoggingInstance = "dataLoggingInstance"
const dataLoggingTag = "dataLoggingTag"

type dataLogging interface {
	Post(tag string, message interface{}) error
}

func attachRoutes(router *gin.Engine) {
	router.GET("/", handleIndex)
	router.POST(uriFormat, handleFeedbackEndpoint)
	router.NoRoute(handleNoRoute)
}

// DataLoggingMiddleware adds dataLoggingInstance and dataLoggingTag contexts to request
func DataLoggingMiddleware(instance dataLogging, loggerTag string) gin.HandlerFunc {
	return func(c *gin.Context) {
		log.Println("Setting middleware DataLogging")
		c.Set(dataLoggingInstance, instance)
		c.Set(dataLoggingTag, loggerTag)
		c.Next()
	}
}

// StartServer starts HTTP server
func StartServer(addr, fluentHost string, fluentPort int, fluentTag string) {
	var err error

	if len(fluentHost) == 0 || fluentPort == 0 {
		log.Println("Cannot detect FluentD address from ENV variable")
		return
	}

	log.Printf("Connecting to FluentD on %s:%d\n", fluentHost, fluentPort)

	logger, err := fluent.New(fluent.Config{
		FluentPort: fluentPort,
		FluentHost: fluentHost,
		MaxRetry:   maxRetryToDeliver,
	})

	if err != nil {
		log.Printf("Cannot start FluentD logger: %s\n", err)
		return
	}

	defer logger.Close()

	router := gin.Default()
	router.Use(DataLoggingMiddleware(logger, fluentTag))
	attachRoutes(router)

	log.Printf("Starting server on %s", addr)
	router.Run(addr)
}
