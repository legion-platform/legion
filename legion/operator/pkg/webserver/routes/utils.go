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

package routes

import (
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	k8_serror "k8s.io/apimachinery/pkg/api/errors"
	"net/http"
	"reflect"
	"strconv"
)

const (
	MaxSize          = 500
	FirstPage        = 0
	SizeUrlParamName = "size"
	PageUrlParamName = "page"
)

type HTTPResult struct {
	// Success of error message
	Message string `json:"message"`
}

// We should develop a custom exception on the storage layer.
// But we rely on kubernetes exceptions for now.
// TODO: implement Legion exceptions
func CalculateHttpStatusCode(err error) int {
	if errStatus, ok := err.(*k8_serror.StatusError); !ok {
		return http.StatusInternalServerError
	} else {
		return int(errStatus.ErrStatus.Code)
	}
}

func UrlParamsToFilter(c *gin.Context, filter interface{}, fields map[string]int) (size int, page int, err error) {
	urlParameters := c.Request.URL.Query()
	size = MaxSize
	page = FirstPage

	for name, value := range urlParameters {
		switch name {
		case SizeUrlParamName:
			if len(value) > 1 {
				return size, page, errors.New("the size URL parameter must be only one")
			}
			size, err = strconv.Atoi(value[0])
			if err != nil {
				return size, page, err
			}
		case PageUrlParamName:
			if len(value) > 1 {
				return size, page, errors.New("the page URL parameter must be only one")
			}
			page, err = strconv.Atoi(value[0])
			if err != nil {
				return size, page, err
			}
		default:
			fieldNumber, ok := fields[name]
			if !ok {
				return size, page, fmt.Errorf("cannot find %s url parameter", name)
			}

			reflect.ValueOf(filter).Elem().Field(fieldNumber).Set(reflect.ValueOf(value))
		}
	}

	return size, page, nil
}
