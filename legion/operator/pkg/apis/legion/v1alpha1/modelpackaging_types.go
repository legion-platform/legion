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

type Target struct {
	Name           string `json:"name"`
	ConnectionName string `json:"connectionName"`
}

// ModelPackagingSpec defines the desired state of ModelPackaging
type ModelPackagingSpec struct {
	ArtifactName *string  `json:"artifactName,omitempty"`
	Type         string   `json:"type"`
	Image        string   `json:"image,omitempty"`
	Arguments    string   `json:"arguments,omitempty"`
	Targets      []Target `json:"targets,omitempty"`
}

type ModelPackagingResult struct {
	// Name of a result. It can be docker image, path to s3 artifact and so on
	Name string `json:"name"`
	// Specific value
	Value string `json:"value"`
}

// ModelPackagingStatus defines the observed state of ModelPackaging
type ModelPackagingStatus struct {
	// Model Packaging State
	State ModelPackagingState `json:"state,omitempty"`
	// Pod exit code
	ExitCode *int32 `json:"exitCode,omitempty"`
	// Pod reason
	Reason *string `json:"reason,omitempty"`
	// Pod last log
	Message *string `json:"message,omitempty"`
	// List of packaing results
	Results []ModelPackagingResult `json:"results,omitempty"`
}

// ModelPackagingState defines current state
type ModelPackagingState string

// These are the valid statuses of pods.
const (
	ModelPackagingScheduling       ModelPackagingState = "scheduling"
	ModelPackagingRunning          ModelPackagingState = "running"
	ModelPackagingSucceeded        ModelPackagingState = "succeeded"
	ModelPackagingFailed           ModelPackagingState = "failed"
	ModelPackagingUnknown          ModelPackagingState = "unknown"
	ModelPackagingArtifactNotFound ModelPackagingState = "artifact_not_found"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelPackaging is the Schema for the modelpackagings API
// +k8s:openapi-gen=true
// +kubebuilder:resource:shortName=mp
type ModelPackaging struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ModelPackagingSpec   `json:"spec,omitempty"`
	Status ModelPackagingStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelPackagingList contains a list of ModelPackaging
type ModelPackagingList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ModelPackaging `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ModelPackaging{}, &ModelPackagingList{})
}
