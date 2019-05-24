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
	gin "github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"log"
)

// ParseRequestDataset extracts all values from HTTP request to key (str) => value (interface{}) map
func ParseRequestDataset(c *gin.Context) map[string]interface{} {
	result := make(map[string]interface{})

	// 1st. Parse form-data
	c.Request.ParseForm()
	if len(c.Request.PostForm) > 0 {
		postBuffer := make(map[string]interface{})
		for key, value := range c.Request.PostForm {
			postBuffer[key] = value
		}
		result["post"] = postBuffer
	}

	// 2nd. Parse URL params
	if uriParameters := c.Request.URL.Query(); len(uriParameters) > 0 {
		uriBuffer := make(map[string]interface{})
		for key, value := range uriParameters {
			uriBuffer[key] = value
		}
		result["uri"] = uriBuffer
	}

	// 3rd. Parse JSON
	if b := binding.Default(c.Request.Method, c.ContentType()); b == binding.JSON {
		var jsonBindingObject interface{}
		if err := c.ShouldBindWith(&jsonBindingObject, b); err == nil {
			result["json"] = jsonBindingObject
		} else {
			log.Printf("Cannot parse JSON: %s", err)
		}
	}

	return result
}
