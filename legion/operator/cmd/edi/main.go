package main

import (
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/legion-platform/legion/legion/operator/pkg/webserver"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("edi-main")

func main() {
	utils.SetupLogger()
	legion.SetUpEDIConfig()

	mainServer, err := webserver.SetUPMainServer()
	if err != nil {
		log.Error(err, "Can't set up edi server")
		os.Exit(1)
	}

	if err := mainServer.Run(":5000"); err != nil {
		log.Error(err, "Server shutdowns")
		os.Exit(1)
	}
}
