package routes

import (
	"github.com/gin-gonic/gin"
)

type HTTPResult struct {
	// Success of error message
	Message string `json:"message"`
}

func AbortWithError(c *gin.Context, code int, message string) {
	c.AbortWithStatusJSON(code, HTTPResult{Message: message})
}

func AbortWithSuccess(c *gin.Context, code int, message string) {
	c.AbortWithStatusJSON(code, HTTPResult{Message: message})
}
