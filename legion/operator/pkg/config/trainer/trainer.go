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
	"github.com/spf13/viper"
	"os"
)

const (
	// The path to the configuration file for a user trainer.
	MTFile = "trainer.mt_file"
	// The path to the dir when a user trainer will save their result.
	OutputTrainingDir = "trainer.output_dir"
	// EDI URL
	EdiURL = "trainer.edi_url"
	// It is a mock for the future. Currently, it is always empty.
	EdiToken = "trainer.edi_token"
	// It is a connection ID, which specifies where a artifact trained artifact is stored.
	OutputConnectionName = "trainer.output_connection"
	// ID of the model training
	ModelTrainingID = "trainer.model_training_id"
)

func init() {
	currentDir, err := os.Getwd()
	if err != nil {
		// Impossible situation
		panic(err)
	}

	viper.SetDefault(OutputTrainingDir, currentDir)
	viper.SetDefault(MTFile, "mt.json")
	viper.SetDefault(EdiURL, "http://localhost:5000")
	viper.SetDefault(EdiToken, "")
	viper.SetDefault(OutputConnectionName, "")
}
