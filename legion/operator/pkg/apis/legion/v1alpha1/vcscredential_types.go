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

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// VCSCredentialSpec defines the desired state of VCSCredential
type VCSCredentialSpec struct {
	// Type of VCS. Currently supports only git.
	// +kubebuilder:validation:Enum=git
	Type string `json:"type"`
	// VCS uri.
	// For Git valid formats are:
	// * git@github.com:legion-platform/legion.git
	Uri string `json:"uri"`
	// Default reference in VCS, e.g. branch, commit, tag and etc.
	DefaultReference string `json:"defaultReference"`
	// Creds for VCS. Is not required. In case of GIT should be base64-encoded private key.
	Credential string `json:"credential,omitempty"`
	// Public keys in base64 format for ssh know hosts. You can gather it using "ssh-keyscan"
	PublicKey string `json:"publicKey,omitempty"`
}

// VCSCredentialStatus defines the observed state of VCSCredential
type VCSCredentialStatus struct {
	SecretName string `json:"secretName,omitempty"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// VCSCredential is the Schema for the vcscredentials API
// +k8s:openapi-gen=true
// +kubebuilder:printcolumn:name="VCS Type",type="string",JSONPath=".spec.type"
// +kubebuilder:printcolumn:name="VCS URI",type="string",JSONPath=".spec.uri"
// +kubebuilder:printcolumn:name="VCS Default reference",type="string",JSONPath=".spec.defaultReference"
// +kubebuilder:resource:shortName=vcs
type VCSCredential struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   VCSCredentialSpec   `json:"spec,omitempty"`
	Status VCSCredentialStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// VCSCredentialList contains a list of VCSCredential
type VCSCredentialList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []VCSCredential `json:"items"`
}

func init() {
	SchemeBuilder.Register(&VCSCredential{}, &VCSCredentialList{})
}
