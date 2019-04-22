package webserver

import (
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver/routes"
	v1Routes "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1"
)

// @title EDI API
// @version 1.0
// @description This is a EDI server.
// @termsOfService http://swagger.io/terms/

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html
func SetUPMainServer() (*gin.Engine, error) {
	server := gin.Default()

	mgr, err := utils.NewManager()
	if err != nil {
		return nil, err
	}

	routes.SetUpHealthCheck(server)
	routes.SetUpSwagger(server)
	routes.SetUpPrometheus(server)
	routes.SetUpIndexPage(server)

	v1Group := server.Group("/api/v1")
	v1Routes.SetupV1Routes(v1Group, mgr.GetClient())

	return server, nil
}
