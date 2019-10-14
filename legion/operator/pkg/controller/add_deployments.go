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

package controller

import (
	"github.com/legion-platform/legion/legion/operator/pkg/controller/modeldeployment"
	"github.com/legion-platform/legion/legion/operator/pkg/controller/modelroute"
	"sigs.k8s.io/controller-runtime/pkg/manager"
)

func init() {
	// AddToManagerDeploymentFuncs is a list of functions to create controllers and add them to a manager.
	AddToManagerDeploymentFuncs = append(AddToManagerDeploymentFuncs, modeldeployment.Add)
	AddToManagerDeploymentFuncs = append(AddToManagerDeploymentFuncs, modelroute.Add)
}

// AddToManagerDeploymentFuncs is a list of functions to add all Controllers to the Manager
var AddToManagerDeploymentFuncs []func(manager.Manager) error

// AddToManager adds all Controllers to the Manager
func AddDeploymentToManager(m manager.Manager) error {
	for _, f := range AddToManagerDeploymentFuncs {
		if err := f(m); err != nil {
			return err
		}
	}
	return nil
}
