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

package service_catalog

import (
	"github.com/gin-gonic/gin"
	_ "github.com/legion-platform/legion/legion/operator/docs"
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog/catalog"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	ginSwagger "github.com/swaggo/gin-swagger"
	"github.com/swaggo/gin-swagger/swaggerFiles"
	"net/http"
)

var handler = ginSwagger.WrapHandler(swaggerFiles.Handler)

func SetUpSwagger(server *gin.Engine, mrCatalog *catalog.ModelRouteCatalog) {
	server.GET("/swagger/*any", func(c *gin.Context) {
		if c.Request.RequestURI == "/swagger/doc.json" {
			docJson, err := mrCatalog.ProcessSwaggerJson()
			if err != nil {
				c.AbortWithStatusJSON(
					http.StatusInternalServerError,
					routes.HTTPResult{Message: err.Error()},
				)
			}

			_, err = c.Writer.Write(docJson)
			if err != nil {
				c.AbortWithStatusJSON(
					http.StatusInternalServerError,
					routes.HTTPResult{Message: err.Error()},
				)
			}
		} else {
			handler(c)
		}
	})
}
