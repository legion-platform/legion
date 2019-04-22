package routes

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

const (
	healthCheckURL = "/health"
)

func healthCheck(c *gin.Context) {
	c.AbortWithStatusJSON(http.StatusOK, gin.H{})
}

func SetUpHealthCheck(server *gin.Engine) {
	server.GET(healthCheckURL, healthCheck)
}
