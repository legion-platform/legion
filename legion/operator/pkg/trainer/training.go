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
	train_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/training"
)

func LogInfo(trainStorage train_storage.Storage, training *training.K8sTrainer, info map[string]string) error {
	log.Info("Update information", "training", training, "info", info)

	return nil
}

func SaveInfo(trainStorage train_storage.Storage, training *training.K8sTrainer, info map[string]string) error {
	return trainStorage.SaveModelTrainingInfo(training.ModelTraining.Id, info)
}
