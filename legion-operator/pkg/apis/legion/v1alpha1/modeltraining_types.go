/*

   Copyright 2019 EPAM Systems

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

*/

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ModelTrainingSpec defines the desired state of ModelTraining
type ModelTrainingSpec struct {
	// Type of toolchain. Currently supports only python.
	// +kubebuilder:validation:Enum=python
	ToolchainType       string   `json:"toolchain"`
	Entrypoint          string   `json:"entrypoint"`
	EntrypointArguments []string `json:"args,omitempty"`
	// Custom environment variables that should be setted before entrypoint invocation.
	// In ENVname:value format
	CustomENV map[string]string `json:"env,omitempty"`
	// Model training hyperparameters in parameter:value format
	Hyperparameters map[string]string `json:"hyperparameters,omitempty"`
	// Name of VCSCredential resource. Must exists
	VCSName string `json:"vcsName"`
	// Custom VCS reference for VCSCredential
	VCSRef string `json:"vcsRef,omitempty"`
	// Train image
	Image string `json:"image,omitempty"`
}

// ModelTrainingState defines current state
type ModelTrainingState string

// These are the valid statuses of pods.
const (
	ModelTrainingScheduling   ModelTrainingState = "scheduling"
	ModelTrainingFetchingCode ModelTrainingState = "fetching-code"
	ModelTrainingRunning      ModelTrainingState = "running"
	ModelTrainingCapturing    ModelTrainingState = "capturing"
	ModelTrainingSucceeded    ModelTrainingState = "succeeded"
	ModelTrainingFailed       ModelTrainingState = "failed"
	ModelTrainingUnknown      ModelTrainingState = "unknown"
)

// ModelTrainingStatus defines the observed state of ModelTraining
type ModelTrainingStatus struct {
	// +kubebuilder:validation:Enum=scheduling,fetching-code,running,capturing,succeeded,failed,unknown
	TrainingState ModelTrainingState `json:"state,omitempty"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelTraining is the Schema for the modeltrainings API
// +k8s:openapi-gen=true
// +kubebuilder:printcolumn:name="Toolchain",type="string",JSONPath=".spec.toolchain"
// +kubebuilder:printcolumn:name="Entrypoint",type="string",JSONPath=".spec.entrypoint"
// +kubebuilder:printcolumn:name="VCS name",type="string",JSONPath=".spec.vcsName"
// +kubebuilder:printcolumn:name="Image",type="string",JSONPath=".spec.image"
// +kubebuilder:resource:shortName=mt
type ModelTraining struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ModelTrainingSpec   `json:"spec,omitempty"`
	Status ModelTrainingStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelTrainingList contains a list of ModelTraining
type ModelTrainingList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ModelTraining `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ModelTraining{}, &ModelTrainingList{})
}
