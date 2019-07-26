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
	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type packagingK8sStorage struct {
	k8sClient   client.Client
	k8sConfig   *rest.Config
	namespace   string
	piNamespace string
}

func NewStorage(namespace, piNamespace string, k8sClient client.Client, k8sConfig *rest.Config) mp_storage.Storage {
	return &packagingK8sStorage{
		namespace:   namespace,
		k8sClient:   k8sClient,
		piNamespace: piNamespace,
		k8sConfig:   k8sConfig,
	}
}
