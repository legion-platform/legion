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
	"fmt"
	"github.com/gin-gonic/gin"
	config_deployment "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/spf13/viper"
	"net/http"
)

const (
	authHeaderName = "X-Jwt"
)

func SetUpIndexPage(server *gin.Engine) {
	// TODO: replace with https://github.com/jessevdk/go-assets
	server.LoadHTMLGlob(fmt.Sprintf("%s/*", viper.GetString(config_deployment.ServerTemplateFolder)))

	server.GET("/", func(c *gin.Context) {
		token := c.GetHeader(authHeaderName)

		c.HTML(http.StatusOK, "index.html", gin.H{
			"token": token,
		})
	})
}
