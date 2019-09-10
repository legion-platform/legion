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

package catalog

import (
	"bytes"
	"encoding/json"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
	"sync"
	"text/template"
)

var log = logf.Log.WithName("catalog")

type ModelRouteCatalog struct {
	sync.RWMutex
	routes map[string]map[string]interface{}
}

func NewModelRouteCatalog() *ModelRouteCatalog {
	return &ModelRouteCatalog{
		routes: map[string]map[string]interface{}{},
	}
}

func (mdc *ModelRouteCatalog) AddModelRoute(mr *v1alpha1.ModelRoute, infoResponse []byte) error {
	mdc.Lock()
	defer mdc.Unlock()

	modelSwagger := map[string]interface{}{}
	if err := json.Unmarshal(infoResponse, &modelSwagger); err != nil {
		log.Error(err, "Unmarshal swagger model", "mr id", mr.Name)
		return err
	}
	paths := modelSwagger["paths"].(map[string]interface{})

	for url, method := range paths {
		realUrl := mr.Spec.UrlPrefix + url

		realMethod := method.(map[string]interface{})
		for _, content := range realMethod {
			realContent := content.(map[string]interface{})
			realContent["tags"] = []string{mr.Name}
		}

		mdc.routes[realUrl] = realMethod
	}

	return nil
}

func (mdc *ModelRouteCatalog) DeleteModelRoute(mr *v1alpha1.ModelRoute) {
	mdc.Lock()
	defer mdc.Unlock()

	for url := range mdc.routes {
		if strings.HasSuffix(url, mr.Spec.UrlPrefix) {
			delete(mdc.routes, url)
		}
	}
}

func (mdc *ModelRouteCatalog) ProcessSwaggerJson() ([]byte, error) {
	mdc.RLock()
	defer mdc.RUnlock()

	routesBytes, err := json.Marshal(&mdc.routes)
	if err != nil {
		return nil, err
	}

	var buff bytes.Buffer
	if err := swaggerTemplate.Execute(&buff, string(routesBytes)); err != nil {
		return nil, err
	} else {
		return buff.Bytes(), nil
	}
}

func init() {
	tmpl, err := template.New("swagger template").Parse(templateStr)
	if err != nil {
		panic(err)
	}

	swaggerTemplate = tmpl
}

const templateStr = `
{
    "swagger": "2.0",
    "info": {
        "description": "Catalog of model services",
        "title": "EDGE API",
        "termsOfService": "http://swagger.io/terms/",
        "contact": {},
        "license": {
            "name": "Apache 2.0",
            "url": "http://www.apache.org/licenses/LICENSE-2.0.html"
        },
        "version": "1.0"
    },
    "schemes": [
      "https",
    ],
    "host": "",
    "basePath": "",
    "paths": {{ . }}
}
`

var swaggerTemplate *template.Template
