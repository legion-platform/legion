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
	"github.com/spf13/viper"
)

const (
	// The path to the configuration file for a user packager.
	MPFile = "packager.mp_file"
	// The path to the dir when a user packager will save their result.
	OutputPackagingDir = "packager.output_dir"
	// EDI URL
	EdiURL = "packager.edi_url"
	// It is a mock for the future. Currently, it is always empty.
	EdiToken = "packager.edi_token"
	// ID of the model packaging
	ModelPackagingID = "packager.model_packaging_id"
	// It is a connection ID, which specifies where a artifact trained artifact is stored.
	OutputConnectionName = "packager.output_connection"
)

func init() {
	viper.SetDefault(OutputPackagingDir, "output")
	viper.SetDefault(MPFile, "mp.json")
	viper.SetDefault(EdiURL, "http://localhost:5000")
	viper.SetDefault(EdiToken, "")
	viper.SetDefault(OutputConnectionName, "")
}
