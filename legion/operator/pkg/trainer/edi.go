/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package trainer

import (
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	trainer_conf "github.com/legion-platform/legion/legion/operator/pkg/config/trainer"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
)

// The function extracts data from a repository and creates the training entity.
func (mt *ModelTrainer) getTraining() (*training.K8sTrainer, error) {
	modelTraining, err := mt.trainRepo.GetModelTraining(mt.modelTrainingID)
	if err != nil {
		return nil, err
	}

	vcs, err := mt.connRepo.GetConnection(modelTraining.Spec.VCSName)
	if err != nil {
		return nil, err
	}

	inputData := make([]training.InputDataBindingDir, 0, len(modelTraining.Spec.Data))
	for _, trainData := range modelTraining.Spec.Data {
		var trainDataConnSpec legionv1alpha1.ConnectionSpec

		trainDataConn, err := mt.connRepo.GetConnection(trainData.Connection)
		if err != nil {
			mt.log.Error(err, "Get train data", legion.ConnectionIDLogPrefix, trainData.Connection)

			return nil, err
		}

		trainDataConnSpec = trainDataConn.Spec

		inputData = append(inputData, training.InputDataBindingDir{
			LocalPath:   trainData.LocalPath,
			RemotePath:  trainData.RemotePath,
			DataBinding: trainDataConnSpec,
		})
	}

	outputConn, err := mt.connRepo.GetConnection(viper.GetString(trainer_conf.OutputConnectionName))
	if err != nil {
		return nil, err
	}

	ti, err := mt.trainRepo.GetToolchainIntegration(modelTraining.Spec.Toolchain)
	if err != nil {
		return nil, err
	}

	return &training.K8sTrainer{
		VCS:        vcs,
		InputData:  inputData,
		OutputConn: outputConn,
		ModelTraining: &training.ModelTraining{
			ID:   modelTraining.ID,
			Spec: modelTraining.Spec,
		},
		ToolchainIntegration: ti,
	}, nil
}
