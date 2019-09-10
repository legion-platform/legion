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
	"github.com/legion-platform/legion/legion/operator/pkg/service_catalog/catalog"
)

// @title EDI API
// @version 1.0
// @description This is a EDI server.
// @termsOfService http://swagger.io/terms/

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html
func SetUPMainServer(mrc *catalog.ModelRouteCatalog) (*gin.Engine, error) {
	server := gin.Default()

	SetUpSwagger(server, mrc)
	SetUpHealthCheck(server)

	return server, nil
}
