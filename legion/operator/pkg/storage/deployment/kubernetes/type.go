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

package kubernetes

import (
	md_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/deployment"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

var (
	DefaultMDDeleteOption = metav1.DeletePropagationForeground
)

type deploymentK8sStorage struct {
	k8sClient      client.Client
	mdDeleteOption metav1.DeletionPropagation
	namespace      string
}

func NewStorage(namespace string, k8sClient client.Client) md_storage.Storage {
	return NewStorageWithOptions(namespace, k8sClient, DefaultMDDeleteOption)
}

func NewStorageWithOptions(namespace string, k8sClient client.Client, mdDeleteOption metav1.DeletionPropagation) md_storage.Storage {
	return &deploymentK8sStorage{
		namespace:      namespace,
		k8sClient:      k8sClient,
		mdDeleteOption: mdDeleteOption,
	}
}
