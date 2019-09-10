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

package packaging

import "github.com/legion-platform/legion/legion/operator/pkg/apis/connection"

type PackagerTarget struct {
	// Target name
	Name string `json:"name"`
	// A Connection for this target
	Connection connection.Connection `json:"connection"`
}

type K8sPackager struct {
	// Connection where a trained model artifact is stored
	ModelHolder *connection.Connection `json:"modelHolder"`
	// Model Packaging
	ModelPackaging *ModelPackaging `json:"modelPackaging"`
	// Packaging integration
	PackagingIntegration *PackagingIntegration `json:"packagingIntegration"`
	// Name of trained model artifact name
	TrainingZipName string `json:"trainingZipName"`
	// List of targets with appropriate connections
	Targets []PackagerTarget `json:"targets"`
}
