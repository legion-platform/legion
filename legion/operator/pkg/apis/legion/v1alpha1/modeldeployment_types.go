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
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ModelDeploymentSpec defines the desired state of ModelDeployment
type ModelDeploymentSpec struct {
	// Model Docker image
	Image string `json:"image"`
	// Resources for model deployment
	// The same format like k8s uses for pod resources.
	Resources *v1.ResourceRequirements `json:"resources,omitempty"`
	// Annotations for model pods.
	Annotations map[string]string `json:"annotations,omitempty"`
	// Number of pods for model. By default the replicas parameter equals 1.
	Replicas *int32 `json:"replicas,omitempty"`
	// Initial delay for liveness probe of model pod
	LivenessProbeInitialDelay *int32 `json:"livenessProbeInitialDelay,omitempty"`
	// Initial delay for readiness probe of model pod
	ReadinessProbeInitialDelay *int32 `json:"readinessProbeInitialDelay,omitempty"`
}

type ModelDeploymentState string

const (
	ModelDeploymentFailed  ModelDeploymentState = "DeploymentFailed"
	ModelDeploymentCreated ModelDeploymentState = "DeploymentCreated"
)

// ModelDeploymentStatus defines the observed state of ModelDeployment
type ModelDeploymentStatus struct {
	// The state of a model deployment.
	//   "DeploymentFailed" - A model was not deployed. Because some parameters of the
	//                        custom resource are wrong. For example, there is not a model
	//                        image in a Docker registry.
	//   "DeploymentCreated" - A model was deployed successfully.
	State ModelDeploymentState `json:"state,omitempty"`
	// The message describes the state in more details.
	Message string `json:"message,omitempty"`
	// The model k8s deployment name
	Deployment string `json:"deployment,omitempty"`
	// The model k8s service name
	Service string `json:"service,omitempty"`
	// The model k8s service name
	ServiceURL string `json:"serviceURL,omitempty"`
	// Number of available pods
	AvailableReplicas int32 `json:"availableReplicas,omitempty"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelDeployment is the Schema for the modeldeployments API
// +k8s:openapi-gen=true
// +kubebuilder:printcolumn:name="State",type="string",JSONPath=".status.state"
// +kubebuilder:printcolumn:name="Model image",type="string",JSONPath=".spec.image"
// +kubebuilder:printcolumn:name="Service URL",type="string",JSONPath=".status.serviceURL"
// +kubebuilder:printcolumn:name="Available Replicas",type="string",JSONPath=".status.availableReplicas"
// +kubebuilder:resource:shortName=md
type ModelDeployment struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ModelDeploymentSpec   `json:"spec,omitempty"`
	Status ModelDeploymentStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ModelDeploymentList contains a list of ModelDeployment
type ModelDeploymentList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ModelDeployment `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ModelDeployment{}, &ModelDeploymentList{})
}
