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

package trainer

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"github.com/legion-platform/legion/legion/operator/pkg/buildah"
	trainer_conf "github.com/legion-platform/legion/legion/operator/pkg/config/trainer"
	uuid "github.com/nu7hatch/gouuid"
	"github.com/spf13/viper"
)

func TrainOnBuildah(mtFilePath string, training *training.K8sTrainer) error {
	u4, err := uuid.NewV4()
	if err != nil {
		log.Error(err, "UUID generating")
		return err
	}
	containerName := u4.String()

	log.Info("Start pulling base image")
	if err := buildah.FromCmd(
		buildah.ContainerNameFromArg(containerName),
		buildah.BaseImageFromArg(training.ModelTraining.Spec.Image),
	); err != nil {
		log.Error(err, "Pulling is failed")
		return err
	}

	targetDir := viper.GetString(trainer_conf.TargetPath)
	if err := buildah.ConfigCmd(
		buildah.ContainerNameConfigArg(containerName),
		buildah.EnvsConfigArg(training.ToolchainIntegration.Spec.AdditionalEnvironments),
		buildah.WorkingDirConfigArg(targetDir),
	); err != nil {
		log.Error(err, "Envs adding is failed")
		return err
	}

	if err := buildah.RunCmd(
		buildah.ContainerNameRunArg(containerName),
		buildah.UserRunArg("0:0"),
		buildah.NetworkRunArg("host"),
		buildah.VolumeRunArg(targetDir, targetDir),
		buildah.CommandRunArg(training.ToolchainIntegration.Spec.Entrypoint,
			"--verbose",
			"--mt", mtFilePath,
			"--target", viper.GetString(trainer_conf.OutputTrainingDir)),
	); err != nil {
		log.Error(err, "Training failed")
		return err
	}

	return nil
}
