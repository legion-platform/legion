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
	"sync"
	"text/template"
)

var log = logf.Log.WithName("catalog")

type ModelRouteInfo struct {
	Data map[string]map[string]interface{}
}

type ModelRouteCatalog struct {
	sync.RWMutex
	routes map[string]*ModelRouteInfo
}

func NewModelRouteCatalog() *ModelRouteCatalog {
	return &ModelRouteCatalog{
		routes: map[string]*ModelRouteInfo{},
	}
}

func (mdc *ModelRouteCatalog) AddModelRoute(mr *v1alpha1.ModelRoute, infoResponse []byte) error {
	mdc.Lock()
	defer mdc.Unlock()
	log.Info("Add model route", "model route id", mr.Name)

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

		log.Info("Add model url", "model url", realUrl, "model route id", mr.Name)

		mri, ok := mdc.routes[mr.Name]
		if !ok {
			mri = &ModelRouteInfo{}
			mri.Data = make(map[string]map[string]interface{})
			mdc.routes[mr.Name] = mri
		}

		mri.Data[realUrl] = realMethod
	}

	return nil
}

func (mdc *ModelRouteCatalog) UpdateModelRouteCatalog(mrList *v1alpha1.ModelRouteList) {
	mdc.Lock()
	defer mdc.Unlock()

	routes := map[string]*ModelRouteInfo{}
	for _, mr := range mrList.Items {
		if data, ok := mdc.routes[mr.Name]; ok {
			log.Info("Stay alive model route", "model route id", mr.Name)

			routes[mr.Name] = data
		}
	}

	mdc.routes = routes
}

func (mdc *ModelRouteCatalog) DeleteModelRoute(mrName string) {
	mdc.Lock()
	defer mdc.Unlock()
	log.Info("Delete model route", "model route id", mrName)

	delete(mdc.routes, mrName)
}

func (mdc *ModelRouteCatalog) ProcessSwaggerJson() ([]byte, error) {
	mdc.RLock()
	defer mdc.RUnlock()
	allUrls := map[string]map[string]interface{}{}

	for _, mri := range mdc.routes {
		for url, data := range mri.Data {
			allUrls[url] = data
		}
	}

	routesBytes, err := json.Marshal(allUrls)
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
        "title": "Service Catalog",
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
