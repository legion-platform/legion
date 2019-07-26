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
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type DataBindingDir struct {
	// Connection name for data
	Connection string `json:"connName"`
	// Local training path
	LocalPath string `json:"localPath"`
	// Overwrite remote data path in connection
	RemotePath string `json:"remotePath,omitempty"`
}

type ModelIdentity struct {
	// Model name
	Name string `json:"name"`
	// Model version
	Version string `json:"version"`
	// Template of output artifact name
	ArtifactNameTemplate string `json:"artifactNameTemplate,omitempty"`
}

// ModelTrainingSpec defines the desired state of ModelTraining
type ModelTrainingSpec struct {
	// Model Identity
	Model ModelIdentity `json:"model"`
	// IntegrationName of toolchain
	Toolchain string `json:"toolchain"`
	// Custom environment variables that should be set before entrypoint invocation.
	CustomEnvs []EnvironmentVariable `json:"envs,omitempty"`
	// Model training hyperParameters in parameter:value format
	HyperParameters map[string]string `json:"hyperParameters,omitempty"`
	// Directory with model scripts/files in a git repository
	WorkDir string `json:"workDir,omitempty"`
	// Model training file. It can be python\bash script or jupiter notebook
	Entrypoint          string   `json:"entrypoint"`
	EntrypointArguments []string `json:"args,omitempty"`
	// Name of Connection resource. Must exists
	VCSName string `json:"vcsName"`
	// Train image
	Image string `json:"image,omitempty"`
	// VCS Reference
	Reference string `json:"reference,omitempty"`
	// Resources for model container
	// The same format like k8s uses for pod resources.
	Resources *ResourceRequirements `json:"resources,omitempty"`
	// Input data for a training
	Data []DataBindingDir `json:"data,omitempty"`
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

type TrainingResult struct {
	// Mlflow run ID
	RunID string `json:"runId"`
	// Trained artifact name
	ArtifactName string `json:"artifactName"`
	// VCS commit
	CommitID string `json:"commitID"`
}

// ModelTrainingStatus defines the observed state of ModelTraining
type ModelTrainingStatus struct {
	// Model Packaging State
	State ModelTrainingState `json:"state,omitempty"`
	// Pod exit code
	ExitCode *int32 `json:"exitCode,omitempty"`
	// Pod reason
	Reason *string `json:"reason,omitempty"`
	// Pod last log
	Message *string `json:"message,omitempty"`
	// List of training results
	Artifacts []TrainingResult `json:"artifacts,omitempty"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelTraining is the Schema for the modeltrainings API
// +k8s:openapi-gen=true
// +kubebuilder:printcolumn:name="Status",type="string",JSONPath=".status.state"
// +kubebuilder:printcolumn:name="Toolchain",type="string",JSONPath=".spec.toolchain"
// +kubebuilder:printcolumn:name="VCS name",type="string",JSONPath=".spec.vcsName"
// +kubebuilder:printcolumn:name="Model name",type="string",JSONPath=".status.modelName"
// +kubebuilder:printcolumn:name="Model version",type="string",JSONPath=".status.modelVersion"
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
