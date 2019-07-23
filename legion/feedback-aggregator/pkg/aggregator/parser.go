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
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	// 2 MB
	memoryForParsedForm = 2 << 20
)

var logP = logf.Log.WithName("aggregator-parser")

// ParseRequestDataset extracts all values from HTTP request to key (str) => value (interface{}) map
func ParseRequestDataset(c *gin.Context) (map[string]interface{}, error) {
	result := make(map[string]interface{})

	// 1st. Parse multipart/form-data
	if err := c.Request.ParseMultipartForm(memoryForParsedForm); err != nil {
		logP.Error(err, "multipart/form-data parsing failed")
	} else if c.Request.MultipartForm != nil {
		postBuffer := make(map[string]interface{})
		for key, values := range c.Request.MultipartForm.Value {
			for value := range values {
				postBuffer[key] = value
			}
		}
		result["post"] = postBuffer
	}

	// 2st. Parse urlencoded
	if err := c.Request.ParseForm(); err != nil {
		logP.Error(err, "urlencoded parsing failed")
	} else if len(c.Request.PostForm) > 0 {
		postBuffer := make(map[string]interface{})
		for key, value := range c.Request.PostForm {
			postBuffer[key] = value
		}
		result["post"] = postBuffer
	}

	// 3nd. Parse URL params
	if uriParameters := c.Request.URL.Query(); len(uriParameters) > 0 {
		uriBuffer := make(map[string]interface{})
		for key, value := range uriParameters {
			uriBuffer[key] = value
		}
		result["uri"] = uriBuffer
	}

	// 4rd. Parse JSON
	if b := binding.Default(c.Request.Method, c.ContentType()); b == binding.JSON {
		var jsonBindingObject interface{}
		if err := c.ShouldBindWith(&jsonBindingObject, b); err == nil {
			result["json"] = jsonBindingObject
		} else {
			logP.Error(err, "Cannot parse JSON")

			return nil, err
		}
	}

	return result, nil
}
