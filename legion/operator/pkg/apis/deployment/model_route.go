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

package deployment

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
)

type ModelRoute struct {
	// Model route id
	Id string `json:"id"`
	// Model route specification
	Spec v1alpha1.ModelRouteSpec `json:"spec,omitempty"`
	// Model route status
	Status *v1alpha1.ModelRouteStatus `json:"status,omitempty"`
}
