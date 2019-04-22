package routes

import (
	"github.com/gin-gonic/gin"
	"github.com/zsais/go-gin-prometheus"
	"strings"
)

func SetUpPrometheus(server *gin.Engine) {
	p := ginprometheus.NewPrometheus("gin")
	p.ReqCntURLLabelMappingFn = func(c *gin.Context) string {
		url := c.Request.URL.String()
		for _, p := range c.Params {
			if p.Key == "name" {
				url = strings.Replace(url, p.Value, ":name", 1)
				break
			}
		}
		return url
	}

	p.Use(server)
}
