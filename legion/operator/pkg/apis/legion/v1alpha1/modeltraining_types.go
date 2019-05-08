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

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ModelTrainingSpec defines the desired state of ModelTraining
type ModelTrainingSpec struct {
	// Type of toolchain. Currently supports only python.
	// +kubebuilder:validation:Enum=python,jupyter
	ToolchainType string `json:"toolchain"`
	// Custom environment variables that should be setted before entrypoint invocation.
	// In ENVname:value format
	CustomEnvs map[string]string `json:"env,omitempty"`
	// Model training hyperparameters in parameter:value format
	Hyperparameters map[string]string `json:"hyperparameters,omitempty"`
	// Model training file. It can be python\bash script or jupiter notebook
	Entrypoint          string   `json:"entrypoint"`
	EntrypointArguments []string `json:"args,omitempty"`
	// Name of VCSCredential resource. Must exists
	VCSName string `json:"vcsName"`
	// Train image
	Image string `json:"image,omitempty"`
	// Model file
	ModelFile string `json:"modelFile,omitempty"`
	// VCS Reference
	Reference string `json:"reference,omitempty"`
	// Resources for model container
	// The same format like k8s uses for pod resources.
	Resources *corev1.ResourceRequirements `json:"resources,omitempty"`
}

// ModelTrainingState defines current state
type ModelTrainingState string

// These are the valid statuses of pods.
const (
	ModelTrainingScheduling ModelTrainingState = "scheduling"
	ModelTrainingRunning    ModelTrainingState = "running"
	ModelTrainingSucceeded  ModelTrainingState = "succeeded"
	ModelTrainingFailed     ModelTrainingState = "failed"
	ModelTrainingUnknown    ModelTrainingState = "unknown"
)

// ModelTrainingStatus defines the observed state of ModelTraining
type ModelTrainingStatus struct {
	// +kubebuilder:validation:Enum=scheduling,fetching-code,running,capturing,succeeded,failed,unknown
	TrainingState ModelTrainingState `json:"state,omitempty"`
	ModelImage    string             `json:"modelImage,omitempty"`
	ModelID       string             `json:"id,omitempty"`
	ModelVersion  string             `json:"version,omitempty"`
	ExitCode      int32              `json:"exitCode,omitempty"`
	Reason        string             `json:"reason,omitempty"`
	Message       string             `json:"message,omitempty"`
	PodName       string             `json:"podName,omitempty"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelTraining is the Schema for the modeltrainings API
// +k8s:openapi-gen=true
// +kubebuilder:printcolumn:name="Status",type="string",JSONPath=".status.state"
// +kubebuilder:printcolumn:name="Toolchain",type="string",JSONPath=".spec.toolchain"
// +kubebuilder:printcolumn:name="VCS name",type="string",JSONPath=".spec.vcsName"
// +kubebuilder:printcolumn:name="ID",type="string",JSONPath=".status.id"
// +kubebuilder:printcolumn:name="Version",type="string",JSONPath=".status.version"
// +kubebuilder:printcolumn:name="Model image",type="string",JSONPath=".status.modelImage"
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
