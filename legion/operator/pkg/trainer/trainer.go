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
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	trainer_conf "github.com/legion-platform/legion/legion/operator/pkg/config/trainer"
	train_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
	"gopkg.in/yaml.v2"
	"path"
	"path/filepath"

	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/rclone"

	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"io/ioutil"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	log = logf.Log.WithName("trainer")
)

const (
	modelTrainingFile = "mt.json"
)

type ModelTrainer struct {
	trainingFunc    Train
	updateTrainInfo UpdateTrainInfo
	trainStorage    train_storage.Storage
}

func NewModelTrainer(storage train_storage.Storage) (*ModelTrainer, error) {
	return &ModelTrainer{
		trainingFunc:    TrainOnBuildah,
		updateTrainInfo: SaveInfo,
		trainStorage:    storage,
	}, nil
}

// ModelConfig build contains the following steps:
//   1) Download specified git repository to the shared directory between model and trainer pods
//   2) Start model entrypoint script\playbook
//   3) Extract model information from model file and save in annotations of current pod
//   3) Launch legionctl command to build a model docker image
func (mb *ModelTrainer) Start() (err error) {
	k8sTraining, err := getTraining()
	if err != nil {
		return err
	}

	// TODO: doesn't hardcode on git
	commitID, err := CloneUserRepo(k8sTraining)
	if err != nil {
		log.Error(err, "Error occurs during cloning project")
		return err
	}

	if err := mb.updateTrainInfo(mb.trainStorage, k8sTraining, map[string]string{
		legion.ModelCommitID: commitID,
	}); err != nil {
		log.Error(err, "Cannot save the commit id")
	}

	targetDir := viper.GetString(trainer_conf.TargetPath)
	log.Info("Change current working dir", "new worker dir", targetDir)
	if err := os.Chdir(targetDir); err != nil {
		log.Error(err, "Changing current working dir failed", "new worker dir", targetDir)
		return err
	}

	if err := mb.downloadData(k8sTraining); err != nil {
		log.Error(err, "Downloading training data failed", "mt name", targetDir)
		return err
	}

	mtBytes, err := json.Marshal(k8sTraining)
	if err != nil {
		return err
	}

	err = ioutil.WriteFile(modelTrainingFile, mtBytes, 0644)
	if err != nil {
		return err
	}

	if err := mb.trainingFunc(modelTrainingFile, k8sTraining); err != nil {
		log.Error(err, "Starting of training failed")

		return err
	}

	if err := mb.saveResult(k8sTraining, commitID); err != nil {
		return err
	}

	return
}

func getTraining() (*training.K8sTrainer, error) {
	k8sTraining := &training.K8sTrainer{}

	k8sTrainingFile, err := os.Open(viper.GetString(trainer_conf.MTFile))
	if err != nil {
		return nil, err
	}

	k8sTrainingBytes, err := ioutil.ReadAll(k8sTrainingFile)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal(k8sTrainingBytes, k8sTraining)
	if err != nil {
		return nil, err
	}

	return k8sTraining, nil
}

type trainingDescription struct {
	Output map[string]string `yaml:"output"`
}

func (mb *ModelTrainer) saveResult(training *training.K8sTrainer, commitId string) error {
	outputZipName, err := legion.ProduceTrainingZipName(training.ModelTraining.Spec.Model.ArtifactNameTemplate,
		&legion.TrainingZipNameConfig{
			Name:     training.ModelTraining.Spec.Model.Name,
			Version:  training.ModelTraining.Spec.Model.Version,
			CommitID: commitId,
		})
	if err != nil {
		return err
	}

	outputTrainingDir := viper.GetString(trainer_conf.OutputTrainingDir)
	log.Info("Start to zip the dir", "dir", outputTrainingDir, "archive name",
		outputZipName)

	jsonFile, err := os.Open(filepath.Join(outputTrainingDir, "legion.project.yaml"))
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
		log.Info("Zipping the dir failed", "dir", outputTrainingDir, "archive name",
			outputZipName)
		return err
	}

	storage, err := rclone.NewObjectStorage(&training.OutputConn.Spec)
	if err != nil {
		return err
	}

	if err := storage.Upload(outputZipName, path.Join(storage.RemoteConfig.Path, outputZipName)); err != nil {
		return err
	}

	if err := mb.updateTrainInfo(mb.trainStorage, training, map[string]string{
		legion.TrainingOutputZip: outputZipName,
		legion.TrainingRunId:     trainingDesc.Output["run_id"],
	}); err != nil {
		log.Error(err, "Cannot save the annotations on pod")
	}

	return nil
}

func (mb *ModelTrainer) downloadData(training *training.K8sTrainer) error {
	if len(training.InputData) == 0 {
		log.Info("Model training data is empty. Skip downloading", "mt id", training.ModelTraining.Id)

		return nil
	}
	for _, mtData := range training.InputData {
		log.Info("Start download training data",
			"mt id", training.ModelTraining.Id,
			"remote path", mtData.RemotePath,
			"local path", mtData.LocalPath,
			"connection type", mtData.DataBinding.Type,
			"connection uri", mtData.DataBinding.URI,
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
