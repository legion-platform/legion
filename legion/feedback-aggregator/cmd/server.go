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

package main

import (
	"flag"
	"log"
	"os"
	"strconv"

	utils "github.com/legion-platform/legion/legion/feedback-aggregator/pkg/utils"
)

const (
	fluentEnvHost = "FLUENTD_HOST"
	fluentEnvPort = "FLUENTD_PORT"
	fluentEnvTag  = "FLUENTD_TAG"
)

var (
	addr       = flag.String("addr", ":8080", "TCP address to listen to")
	fluentHost = os.Getenv(fluentEnvHost)
	fluentPort = os.Getenv(fluentEnvPort)
	fluentTag  = os.Getenv(fluentEnvTag)
)

func main() {
	flag.Parse()

	if len(fluentHost) == 0 || len(fluentPort) == 0 || len(fluentTag) == 0 {
		log.Printf("Please provide values for %s / %s / %s env variables", fluentEnvHost, fluentEnvPort, fluentEnvTag)
		return
	}

	if port, err := strconv.Atoi(fluentPort); err == nil {
		utils.StartServer(*addr, fluentHost, port, fluentTag)
	} else {
		log.Printf("Cannot parse %s (%s): %s", fluentEnvPort, fluentPort, err)
	}
}
