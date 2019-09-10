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
	mt_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type trainingK8sStorage struct {
	k8sClient   client.Client
	k8sConfig   *rest.Config
	namespace   string
	tiNamespace string
}

func NewStorage(namespace, tiNamespace string, k8sClient client.Client, k8sConfig *rest.Config) mt_storage.Storage {
	return &trainingK8sStorage{
		namespace:   namespace,
		tiNamespace: tiNamespace,
		k8sClient:   k8sClient,
		k8sConfig:   k8sConfig,
	}
}
