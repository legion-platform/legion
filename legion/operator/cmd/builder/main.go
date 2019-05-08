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
	"github.com/legion-platform/legion/legion/operator/pkg/builder"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

func main() {
	utils.SetupLogger()

	legion.SetUpBuilderConfig()

	modelBuilder, err := builder.NewModelBuilder()

	if err != nil {
		logf.Log.WithName("builder").Error(err, "Creation of model builder is failed")
		os.Exit(1)
	}

	if err := modelBuilder.Start(); err != nil {
		logf.Log.WithName("builder").Error(err, "Build failed")
		os.Exit(1)
	}
}
