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

type PackagingIntegration struct {
	// Packaging integration id
	ID string `json:"id"`
	// Packaging integration specification
	Spec PackagingIntegrationSpec `json:"spec,omitempty"`
	// Packaging integration status
	Status *v1alpha1.PackagingIntegrationStatus `json:"status,omitempty"`
}

type PackagingIntegrationSpec struct {
	// Path to binary which starts a packaging process
	Entrypoint string `json:"entrypoint"`
	// Default packaging Docker image
	DefaultImage string `json:"defaultImage"`
	// Enable docker privileged flag
	Privileged bool `json:"privileged,omitempty"`
	// Schema which describes targets and arguments for specific packaging integration
	Schema Schema `json:"schema"`
}

type Schema struct {
	// Targets schema
	Targets []v1alpha1.TargetSchema `json:"targets"`
	// Arguments schema
	Arguments JsonSchema `json:"arguments"`
}

type JsonSchema struct {
	// Properties configuration
	Properties []Property `json:"properties"`
	// List of required properties
	Required []string `json:"required,omitempty"`
}

type Property struct {
	// Property name
	Name string `json:"name"`
	// List of property parameters
	Parameters []Parameter `json:"parameters"`
}

type Parameter struct {
	// Parameter name
	Name string `json:"name"`
	// Parameter value
	Value interface{} `json:"value"`
}
