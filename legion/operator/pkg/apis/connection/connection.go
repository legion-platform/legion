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

package connection

import "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"

const (
	S3Type            = v1alpha1.ConnectionType("s3")
	GcsType           = v1alpha1.ConnectionType("gcs")
	AzureBlobType     = v1alpha1.ConnectionType("azureblob")
	GITType           = v1alpha1.ConnectionType("git")
	DockerType        = v1alpha1.ConnectionType("docker")
	EcrType           = v1alpha1.ConnectionType("ecr")
	decryptedDataMask = "*****"
	ResourceTypeName  = "connection"
)

var (
	AllConnectionTypes = []v1alpha1.ConnectionType{
		S3Type, GcsType, AzureBlobType, GITType, DockerType, EcrType,
	}
	AllConnectionTypesSet = map[v1alpha1.ConnectionType]interface{}{}
)

func init() {
	for _, conn := range AllConnectionTypes {
		AllConnectionTypesSet[conn] = nil
	}
}

type Connection struct {
	// Connection id
	ID string `json:"id"`
	// Connection specification
	Spec v1alpha1.ConnectionSpec `json:"spec"`
	// Connection status
	Status *v1alpha1.ConnectionStatus `json:"status,omitempty"`
}

// Replace sensitive data with mask in the connection
func (c *Connection) DeleteSensitiveData() *Connection {
	c.Spec.Password = decryptedDataMask
	c.Spec.KeySecret = decryptedDataMask
	c.Spec.KeyID = decryptedDataMask

	return c
}
