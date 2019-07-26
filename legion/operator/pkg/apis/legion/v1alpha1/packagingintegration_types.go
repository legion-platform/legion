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

type TargetSchema struct {
	Name            string   `json:"name"`
	ConnectionTypes []string `json:"connectionTypes"`
	Required        bool     `json:"required"`
}

type SchemaValidation struct {
	Targets   []TargetSchema `json:"targets,omitempty"`
	Arguments JsonSchema     `json:"arguments"`
}

type JsonSchema struct {
	Properties string   `json:"properties"`
	Required   []string `json:"required,omitempty"`
}

// PackagingIntegrationSpec defines the desired state of PackagingIntegration
type PackagingIntegrationSpec struct {
	Entrypoint   string           `json:"entrypoint"`
	DefaultImage string           `json:"defaultImage,omitempty"`
	Privileged   bool             `json:"privileged,omitempty"`
	Schema       SchemaValidation `json:"schema"`
}

// PackagingIntegrationStatus defines the observed state of PackagingIntegration
type PackagingIntegrationStatus struct {
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// PackagingIntegration is the Schema for the packagingintegrations API
// +k8s:openapi-gen=true
type PackagingIntegration struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   PackagingIntegrationSpec   `json:"spec,omitempty"`
	Status PackagingIntegrationStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// PackagingIntegrationList contains a list of PackagingIntegration
type PackagingIntegrationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []PackagingIntegration `json:"items"`
}

func init() {
	SchemeBuilder.Register(&PackagingIntegration{}, &PackagingIntegrationList{})
}
