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

package training

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
)

type InputDataBindingDir struct {
	// Local path
	LocalPath string `json:"localPath"`
	// Remote path
	RemotePath string `json:"remotePath"`
	// Connection specific for data
	DataBinding v1alpha1.ConnectionSpec `json:"dataBinding"`
}

type K8sTrainer struct {
	// Connection for source code
	VCS *connection.Connection `json:"vcs"`
	// Connection for training data
	InputData []InputDataBindingDir `json:"inputData"`
	// Connection for trained model artifact
	OutputConn *connection.Connection `json:"outputConn"`
	// Model training
	ModelTraining *ModelTraining `json:"modelTraining"`
	// Toolchain integration
	ToolchainIntegration *ToolchainIntegration `json:"toolchainIntegration"`
}
