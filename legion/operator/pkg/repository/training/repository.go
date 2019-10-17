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
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	"io"
	"net/http"
)

const (
	TagKey = "name"
)

type Repository interface {
	GetModelTraining(id string) (*training.ModelTraining, error)
	GetModelTrainingList(options ...kubernetes.ListOption) ([]training.ModelTraining, error)
	GetModelTrainingLogs(id string, writer Writer, follow bool) error
	SaveModelTrainingResult(id string, result *legionv1alpha1.TrainingResult) error
	GetModelTrainingResult(id string) (*legionv1alpha1.TrainingResult, error)
	DeleteModelTraining(id string) error
	UpdateModelTraining(md *training.ModelTraining) error
	CreateModelTraining(md *training.ModelTraining) error
	GetToolchainIntegration(name string) (*training.ToolchainIntegration, error)
	GetToolchainIntegrationList(options ...kubernetes.ListOption) ([]training.ToolchainIntegration, error)
	DeleteToolchainIntegration(name string) error
	UpdateToolchainIntegration(md *training.ToolchainIntegration) error
	CreateToolchainIntegration(md *training.ToolchainIntegration) error
}

type MTFilter struct {
	Toolchain    []string `name:"toolchain"`
	ModelName    []string `name:"model_name"`
	ModelVersion []string `name:"model_version"`
}

type Writer interface {
	http.Flusher
	http.CloseNotifier
	io.Writer
}
