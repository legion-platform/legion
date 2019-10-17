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
	"encoding/json"
	"errors"
	"fmt"
	"github.com/go-logr/logr"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	trainer_conf "github.com/legion-platform/legion/legion/operator/pkg/config/trainer"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/rclone"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	train_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	modelTrainingFile                     = "mt.json"
	unsupportedConnectionTypeErrorMessage = "unexpected connection type: %s. Supported types: git"
	legionProjectFile                     = "legion.project.yaml"
)

type ModelTrainer struct {
	trainRepo       train_repository.Repository
	connRepo        conn_repository.Repository
	modelTrainingID string
	log             logr.Logger
}

func NewModelTrainer(
	trainRepo train_repository.Repository,
	connRepo conn_repository.Repository,
	modelTrainingID string,
) *ModelTrainer {
	trainingLogger := logf.Log.WithName("trainer").
		WithValues(legion.ModelTrainingIDLogPrefix, modelTrainingID)

	return &ModelTrainer{
		trainRepo:       trainRepo,
		connRepo:        connRepo,
		modelTrainingID: modelTrainingID,
		log:             trainingLogger,
	}
}

// This function prepares a training environment. To do this, it performs the following steps:
//   1) It extracts the training entity from repository storage, for example, from the EDI server.
//   2) It downloads the source code of model training.
//   3) The setup function downloads all training data.
//   4) Finally, it saves the training entity to allow an ML toolchain to use it.
func (mt *ModelTrainer) Setup() (err error) {
	// Extracts the training entity
	k8sTraining, err := mt.getTraining()
	if err != nil {
		mt.log.Error(err, "Can not construct the training entity")

		return err
	}

	mt.log.Info("The training entity was constructed successfully")

	commitID := ""

	// Downloads a source code
	switch k8sTraining.VCS.Spec.Type {
	case connection.GITType:
		commitID, err = mt.cloneUserRepo(k8sTraining, viper.GetString(trainer_conf.OutputTrainingDir))
		if err != nil {
			mt.log.Error(err, "Error occurs during cloning project")

			return err
		}
	default:
		return errors.New(unsupportedConnectionTypeErrorMessage)
	}

	mt.log.Info(
		"The model source code was downloaded",
		"dir", viper.GetString(trainer_conf.OutputTrainingDir),
	)

	// Saves some data before starting a training
	if err := mt.trainRepo.SaveModelTrainingResult(
		k8sTraining.ModelTraining.ID,
		&legionv1alpha1.TrainingResult{
			CommitID: commitID,
		},
	); err != nil {
		mt.log.Error(err, "Cannot save the commit id")

		return err
	}

	mt.log.Info("The commit ID was saved", "commit_id", commitID)

	workDir := viper.GetString(trainer_conf.OutputTrainingDir)
	if len(workDir) != 0 {
		mt.log.Info("Change current working dir", "new worker dir", workDir)

		if err := os.Chdir(workDir); err != nil {
			mt.log.Error(err, "Changing current working dir failed",
				"new worker dir", workDir,
			)

			return err
		}
	}

	if err := mt.downloadData(k8sTraining); err != nil {
		mt.log.Error(err, "Downloading training data failed")

		return err
	}

	mt.log.Info("The training data was downloaded")

	// TODO: We make available all connections to a toolchain script. Do we need it?
	mtBytes, err := json.Marshal(k8sTraining)
	if err != nil {
		mt.log.Error(err, "Marshaling of the training entity to JSON format failed.")

		return err
	}

	return ioutil.WriteFile(modelTrainingFile, mtBytes, 0644)
}

type trainingDescription struct {
	Output map[string]string `yaml:"output"`
}

// This function saves a training result. To do this, it performs the following steps:
//   1) It extracts the training entity from repository storage, for example, from the EDI server.
//   2) It creates the training zip archive.
//   2) It uploads the training zip archive to object storage.
//   4) Finally, it saves the training entity results.
func (mt *ModelTrainer) SaveResult() error {
	k8sTraining, err := mt.getTraining()
	if err != nil {
		return err
	}

	mt.log.Info("The training entity was constructed successfully")

	outputZipName, err := legion.ProduceTrainingZipName(
		k8sTraining.ModelTraining.Spec.Model.ArtifactNameTemplate,
		&legion.TrainingZipNameConfig{
			Name:    k8sTraining.ModelTraining.Spec.Model.Name,
			Version: k8sTraining.ModelTraining.Spec.Model.Version,
		},
	)
	if err != nil {
		return err
	}

	outputTrainingDir := viper.GetString(trainer_conf.OutputTrainingDir)
	mt.log.Info("Start to zip the dir", "dir", outputTrainingDir, "archive_name",
		outputZipName)

	jsonFile, err := os.Open(filepath.Join(outputTrainingDir, legionProjectFile))
	if err != nil {
		fmt.Println(err)
	}
	defer jsonFile.Close()

	byteValue, err := ioutil.ReadAll(jsonFile)
	if err != nil {
		return err
	}

	var trainingDesc trainingDescription
	err = yaml.Unmarshal(byteValue, &trainingDesc)
	if err != nil {
		return err
	}

	err = utils.ZipDir(outputTrainingDir, outputZipName)
	if err != nil {
		mt.log.Info("Zipping the dir failed", "dir", outputTrainingDir, "archive name",
			outputZipName)
		return err
	}

	mt.log.Info("Start to zip the dir", "dir", outputTrainingDir, "archive_name",
		outputZipName)

	storage, err := rclone.NewObjectStorage(&k8sTraining.OutputConn.Spec)
	if err != nil {
		return err
	}

	if err := storage.Upload(outputZipName, path.Join(storage.RemoteConfig.Path, outputZipName)); err != nil {
		return err
	}

	if err := mt.trainRepo.SaveModelTrainingResult(
		k8sTraining.ModelTraining.ID,
		&legionv1alpha1.TrainingResult{
			RunID:        trainingDesc.Output["run_id"],
			ArtifactName: outputZipName,
		},
	); err != nil {
		mt.log.Error(err, "Cannot save the training result")
	}

	return nil
}

func (mt *ModelTrainer) downloadData(k8sTraining *training.K8sTrainer) error {
	if len(k8sTraining.InputData) == 0 {
		mt.log.Info("Model k8sTraining data is empty. Skip downloading")

		return nil
	}
	for _, mtData := range k8sTraining.InputData {
		mt.log.Info("Start download k8sTraining data",
			"remote_path", mtData.RemotePath,
			"local_path", mtData.LocalPath,
			"connection_type", mtData.DataBinding.Type,
			"connection_uri", mtData.DataBinding.URI,
		)

		storage, err := rclone.NewObjectStorage(&mtData.DataBinding)
		if err != nil {
			return err
		}

		if err := storage.Download(mtData.LocalPath, mtData.RemotePath); err != nil {
			return err
		}
	}

	return nil
}
