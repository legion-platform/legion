package routes

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	authCookieName = "_oauth2_proxy"
)

var (
	logIndex = logf.Log.WithName("log-index")
)

func SetUpIndexPage(server *gin.Engine) {
	// TODO: replace with https://github.com/jessevdk/go-assets
	server.LoadHTMLGlob(fmt.Sprintf("%s/*", viper.GetString(legion.TemplateFolder)))

	server.GET("/", func(c *gin.Context) {
		token, err := c.Cookie(authCookieName)
		if err != nil {
			logIndex.Error(err, "Token extraction")
			token = ""
		}

		c.HTML(http.StatusOK, "index.html", gin.H{
			"token": token,
		})
	})
}
