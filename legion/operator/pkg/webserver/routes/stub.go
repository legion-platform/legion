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
	_ "github.com/legion-platform/legion/legion/operator/pkg/apis/packaging" //nolint
	_ "github.com/legion-platform/legion/legion/operator/pkg/apis/training"  //nolint
)

// We have some data that doesn't involve in EDI HTTP API,
// but we should generate stub models for this data on another language(python/ts).
// For example, packaging.K8sPackager is the interface between the packager operator and
// the docker-rest packager.
// This hack allows adding some structure to generated swagger documentation.

// @Tags swaggerstub
// @Accept  json
// @Produce  json
// @Success 200 {object} packaging.K8sPackager
// @Success 201 {object} training.K8sTrainer
func stubBuilder() { //nolint
	panic("must be never invoked!")
}
