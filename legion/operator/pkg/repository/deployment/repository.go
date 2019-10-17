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

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
)

const (
	TagKey = "name"
)

type Repository interface {
	GetModelDeployment(name string) (*deployment.ModelDeployment, error)
	GetModelDeploymentList(options ...kubernetes.ListOption) ([]deployment.ModelDeployment, error)
	DeleteModelDeployment(name string) error
	UpdateModelDeployment(md *deployment.ModelDeployment) error
	CreateModelDeployment(md *deployment.ModelDeployment) error
	GetModelRoute(name string) (*deployment.ModelRoute, error)
	GetModelRouteList(options ...kubernetes.ListOption) ([]deployment.ModelRoute, error)
	DeleteModelRoute(name string) error
	UpdateModelRoute(md *deployment.ModelRoute) error
	CreateModelRoute(md *deployment.ModelRoute) error
}

type MdFilter struct {
	RoleName []string `name:"roleName"`
}
