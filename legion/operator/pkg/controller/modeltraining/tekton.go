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

package modeltraining

import (
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	operator_conf "github.com/legion-platform/legion/legion/operator/pkg/config/operator"
	training_conf "github.com/legion-platform/legion/legion/operator/pkg/config/training"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	"github.com/spf13/viper"
	tektonv1alpha1 "github.com/tektoncd/pipeline/pkg/apis/pipeline/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"path"
)

const (
	pathToTrainerBin = "/opt/legion/trainer"
	workspacePath    = "/workspace"
	outputDir        = "output"
)

func generateTrainerTaskSpec(
	trainingCR *legionv1alpha1.ModelTraining,
	toolchainIntegration *training.ToolchainIntegration,
) (*tektonv1alpha1.TaskSpec, error) {
	mainTrainerStep, err := createMainTrainerStep(trainingCR, toolchainIntegration)
	if err != nil {
		return nil, err
	}

	return &tektonv1alpha1.TaskSpec{
		Steps: []tektonv1alpha1.Step{
			createInitTrainerStep(trainingCR.Name),
			mainTrainerStep,
			createResultTrainerStep(trainingCR.Name),
		},
	}, nil
}

func createInitTrainerStep(mtID string) tektonv1alpha1.Step {
	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    legion.TrainerSetupStep,
			Image:   viper.GetString(training_conf.ModelBuilderImage),
			Command: []string{pathToTrainerBin},
			Args: []string{
				"setup",
				"--mt-file",
				path.Join(workspacePath, mtConfig),
				"--mt-id",
				mtID,
				"--output-connection-name",
				viper.GetString(training_conf.OutputConnectionName),
				"--edi-url",
				viper.GetString(operator_conf.EdiURL),
			},
			Resources: trainerResources,
		},
	}
}

func createMainTrainerStep(
	train *legionv1alpha1.ModelTraining,
	trainingIntegration *training.ToolchainIntegration) (tektonv1alpha1.Step, error) {
	trainResources, err := kubernetes.ConvertLegionResourcesToK8s(train.Spec.Resources)
	if err != nil {
		log.Error(err, "The training resources is not valid",
			"mt_id", train.Name, "resources", trainResources)

		return tektonv1alpha1.Step{}, err
	}

	envs := make([]corev1.EnvVar, 0, len(trainingIntegration.Spec.AdditionalEnvironments))
	for name, value := range trainingIntegration.Spec.AdditionalEnvironments {
		envs = append(envs, corev1.EnvVar{
			Name:  name,
			Value: value,
		})
	}

	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    legion.TrainerTrainStep,
			Image:   train.Spec.Image,
			Command: []string{trainingIntegration.Spec.Entrypoint},
			Env:     envs,
			Args: []string{
				"--verbose",
				"--mt",
				path.Join(workspacePath, mtConfig),
				"--target",
				path.Join(workspacePath, outputDir),
			},
			Resources: trainResources,
		},
	}, nil
}

func createResultTrainerStep(mtID string) tektonv1alpha1.Step {
	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    legion.TrainerResultStep,
			Image:   viper.GetString(training_conf.ModelBuilderImage),
			Command: []string{pathToTrainerBin},
			Args: []string{
				"result",
				"--mt-file",
				path.Join(workspacePath, mtConfig),
				"--mt-id",
				mtID,
				"--output-connection-name",
				viper.GetString(training_conf.OutputConnectionName),
				"--edi-url",
				viper.GetString(operator_conf.EdiURL),
				"--output-dir",
				path.Join(workspacePath, outputDir),
			},
			Resources: trainerResources,
		},
	}
}
