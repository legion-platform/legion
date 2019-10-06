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

import "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"

type ModelPackaging struct {
	// Model packaging id
	ID string `json:"id"`
	// Model packaging specification
	Spec ModelPackagingSpec `json:"spec,omitempty"`
	// Model packaging status
	Status *v1alpha1.ModelPackagingStatus `json:"status,omitempty"`
}

// ModelPackagingSpec defines the desired state of ModelPackaging
type ModelPackagingSpec struct {
	// Training output artifact name
	ArtifactName string `json:"artifactName"`
	// Packaging integration ID
	IntegrationName string `json:"integrationName"`
	// Image name. Packaging integration image will be used if this parameters is missed
	Image string `json:"image,omitempty"`
	// List of arguments. This parameter depends on the specific packaging integration
	Arguments map[string]interface{} `json:"arguments"`
	// List of targets. This parameter depends on the specific packaging integration
	Targets []v1alpha1.Target `json:"targets"`
	// Resources for packager container
	// The same format like k8s uses for pod resources.
	Resources *v1alpha1.ResourceRequirements `json:"resources,omitempty"`
}
