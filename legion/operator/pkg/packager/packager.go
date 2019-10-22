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
	"fmt"
	"github.com/go-logr/logr"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/rclone"
	connection_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	packaging_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"io/ioutil"
	"os"
	"path"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	resultFileName     = "result.json"
	modelPackagingFile = "mp.json"
)

type Packager struct {
	packRepo         packaging_repository.Repository
	connRepo         connection_repository.Repository
	log              logr.Logger
	modelPackagingID string
}

func NewPackager(
	packRepo packaging_repository.Repository,
	connRepo connection_repository.Repository,
	modelPackagingID string,
) *Packager {
	return &Packager{
		packRepo: packRepo,
		connRepo: connRepo,
		log: logf.Log.WithName("packager").WithValues(
			legion.ModelPackagingIDLogPrefix, modelPackagingID,
		),
		modelPackagingID: modelPackagingID,
	}
}

// This function prepares a packaging environment. To do this, it performs the following steps:
//   1) It extracts the packaging entity from repository storage, for example, from the EDI server.
//   2) It downloads a trained artifact from object storage.
//   4) Finally, it saves the packaging entity to allow a packager to use it.
func (p *Packager) SetupPackager() (err error) {
	k8sPackaging, err := p.getPackaging()
	if err != nil {
		return err
	}

	if err := p.downloadData(k8sPackaging); err != nil {
		p.log.Error(err, "Downloading packaging data failed")
		return err
	}

	mtBytes, err := json.Marshal(k8sPackaging)
	if err != nil {
		return err
	}

	return ioutil.WriteFile(modelPackagingFile, mtBytes, 0644)
}

// This function saves a packaging result. To do this, it performs the following steps:
//   1) It extracts the packaging entity from repository storage, for example, from the EDI server.
//   2) It reads the packaging result file from workspace.
//   4) Finally, it saves the packaging results.
func (p *Packager) SaveResult() error {
	k8sPackaging, err := p.getPackaging()
	if err != nil {
		return err
	}

	resultFile, err := os.Open(resultFileName)
	if err != nil {
		p.log.Error(err, "Open result file")
		return err
	}
	defer resultFile.Close()

	byteResult, err := ioutil.ReadAll(resultFile)
	if err != nil {
		p.log.Error(err, "Read from result file")
		return err
	}

	var result map[string]string
	if err := json.Unmarshal(byteResult, &result); err != nil {
		p.log.Error(err, "Unmarshal result")
		return err
	}

	packResult := make([]v1alpha1.ModelPackagingResult, 0, len(result))
	for name, value := range result {
		packResult = append(packResult, v1alpha1.ModelPackagingResult{
			Name:  name,
			Value: value,
		})
	}

	return p.packRepo.SaveModelPackagingResult(k8sPackaging.ModelPackaging.ID, packResult)
}

func (p *Packager) downloadData(packaging *packaging.K8sPackager) (err error) {
	fmt.Println(packaging)
	storage, err := rclone.NewObjectStorage(&packaging.ModelHolder.Spec)
	if err != nil {
		p.log.Error(err, "repository creation")

		return err
	}

	file, err := os.Create(packaging.TrainingZipName)
	if err != nil {
		p.log.Error(err, "zip creation")

		return err
	}

	defer func() {
		closeErr := file.Close()
		if closeErr != nil {
			p.log.Error(err, "Error during closing of the file")
		}

		if err == nil {
			err = closeErr
		}
	}()

	if err := storage.Download(
		packaging.TrainingZipName,
		path.Join(storage.RemoteConfig.Path, packaging.TrainingZipName),
	); err != nil {
		p.log.Error(err, "download training zip")

		return err
	}

	if err = os.Mkdir(viper.GetString(packager_conf.OutputPackagingDir), 0777); err != nil {
		p.log.Error(err, "output dir creation")

		return err
	}

	if err := utils.Unzip(packaging.TrainingZipName, viper.GetString(packager_conf.OutputPackagingDir)); err != nil {
		p.log.Error(err, "unzip training data")

		return err
	}

	return nil
}
