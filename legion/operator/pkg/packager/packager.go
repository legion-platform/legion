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

package packager

import (
	"encoding/json"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	"github.com/legion-platform/legion/legion/operator/pkg/rclone"
	packaging_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"io/ioutil"
	"os"
	"path"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	log = logf.Log.WithName("packager")
)

const (
	resultFileName     = "result.json"
	modelPackagingFile = "mp.json"
)

func SetupPackager() (err error) {
	k8sPackaging, err := getPackaging()
	if err != nil {
		return err
	}

	if err := downloadData(k8sPackaging); err != nil {
		log.Error(err, "Downloading packaging data failed", "mp name", k8sPackaging.ModelPackaging.ID)
		return err
	}

	mtBytes, err := json.Marshal(k8sPackaging)
	if err != nil {
		return err
	}

	return ioutil.WriteFile(modelPackagingFile, mtBytes, 0644)
}

func SaveResult(repository packaging_repository.Repository) error {
	k8sPackaging, err := getPackaging()
	if err != nil {
		return err
	}

	resultFile, err := os.Open(resultFileName)
	if err != nil {
		log.Error(err, "Open result file")
		return err
	}
	defer resultFile.Close()

	byteResult, err := ioutil.ReadAll(resultFile)
	if err != nil {
		log.Error(err, "Read from result file")
		return err
	}
	var result map[string]string

	if err := json.Unmarshal(byteResult, &result); err != nil {
		log.Error(err, "Unmarshal result")
		return err
	}

	return repository.SaveModelPackagingResult(k8sPackaging.ModelPackaging.ID, result)
}

func getPackaging() (*packaging.K8sPackager, error) {
	k8sPackaging := &packaging.K8sPackager{}

	k8sPackagingFile, err := os.Open(viper.GetString(packager_conf.MPFile))
	if err != nil {
		return nil, err
	}

	k8sPackagingBytes, err := ioutil.ReadAll(k8sPackagingFile)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal(k8sPackagingBytes, k8sPackaging)
	if err != nil {
		return nil, err
	}

	return k8sPackaging, nil
}

func downloadData(packaging *packaging.K8sPackager) (err error) {
	storage, err := rclone.NewObjectStorage(&packaging.ModelHolder.Spec)
	if err != nil {
		log.Error(err, "repository creation")

		return err
	}

	file, err := os.Create(packaging.TrainingZipName)
	if err != nil {
		log.Error(err, "zip creation")

		return err
	}

	defer func() {
		err = file.Close()
	}()

	if err := storage.Download(
		packaging.TrainingZipName,
		path.Join(storage.RemoteConfig.Path, packaging.TrainingZipName),
	); err != nil {
		log.Error(err, "download training zip")

		return err
	}

	if err = os.Mkdir(viper.GetString(packager_conf.OutputTrainingDir), 0777); err != nil {
		log.Error(err, "output dir creation")

		return err
	}

	if err := utils.Unzip(packaging.TrainingZipName, viper.GetString(packager_conf.OutputTrainingDir)); err != nil {
		log.Error(err, "unzip training data")

		return err
	}

	return nil
}
