package routes

import (
	"github.com/gin-gonic/gin"
	_ "github.com/legion-platform/legion/legion/operator/docs"
	ginSwagger "github.com/swaggo/gin-swagger"
	"github.com/swaggo/gin-swagger/swaggerFiles"
)

const (
	SwaggerHtml = "/swagger/index.html"
)

func SetUpSwagger(server *gin.Engine) {
	server.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}
