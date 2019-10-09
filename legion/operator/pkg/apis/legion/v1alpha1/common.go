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

package v1alpha1

type ResourceList struct {
	// Read more about GPU resource here https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/#using-device-plugins
	GPU *string `json:"gpu,omitempty"`
	// Read more about CPU resource here https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-cpu
	CPU *string `json:"cpu,omitempty"`
	// Read more about memory resource here https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-memory
	Memory *string `json:"memory,omitempty"`
}

type ResourceRequirements struct {
	// Limits describes the maximum amount of compute resources allowed.
	Limits *ResourceList `json:"limits,omitempty"`
	// Requests describes the minimum amount of compute resources required.
	Requests *ResourceList `json:"requests,omitempty"`
}

type EnvironmentVariable struct {
	// Name of an environment variable
	Name string `json:"name"`
	// Value of an environment variable
	Value string `json:"value"`
}
