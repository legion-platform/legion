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

// +genclient

// ConnectionSpec defines the desired state of ConnectionName
type ConnectionSpec struct {
	// Required value. Available values:
	//   * s3
	//   * gcs
	//   * azureblob
	//   * git
	//   * docker
	Type ConnectionType `json:"type"`
	// URI. It is required value
	URI string `json:"uri"`
	// AWS region or GCP project
	Region string `json:"region,omitempty"`
	// Username
	Username string `json:"username,omitempty"`
	// Password
	Password string `json:"password,omitempty"`
	// Service account role
	Role string `json:"role,omitempty"`
	// Key ID
	KeyID string `json:"keyID,omitempty"`
	// SSH or service account secret
	KeySecret string `json:"keySecret,omitempty"`
	// SSH public key
	PublicKey string `json:"publicKey,omitempty"`
	// VCS reference
	Reference string `json:"reference,omitempty"`
	// Custom description
	Description string `json:"description,omitempty"`
	// Custom web UI link
	WebUILink string `json:"webUILink,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type ConnectionType string

// ConnectionStatus defines the observed state of ConnectionName
type ConnectionStatus struct {
	// Kubernetes secret name
	SecretName *string `json:"secretName,omitempty"`
	// Kubernetes service account
	ServiceAccountName *string `json:"serviceAccount,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ConnectionName is the Schema for the connections API
// +k8s:openapi-gen=true
type Connection struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ConnectionSpec   `json:"spec,omitempty"`
	Status ConnectionStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// ConnectionList contains a list of ConnectionName
type ConnectionList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Connection `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Connection{}, &ConnectionList{})
}
