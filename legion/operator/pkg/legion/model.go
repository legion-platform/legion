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

package legion

import (
	"bytes"
	"github.com/pborman/uuid"
	"text/template"
)

type Model struct {
	Name    string `json:"model.name"`
	Version string `json:"model.version"`
}

const (
	ManifestFile      = "manifest.json"
	ModelImageKey     = "model-image"
	ModelNameKey      = "model-name"
	ModelVersionKey   = "model-version"
	ModelCommitID     = "model-commit-id"
	TrainingOutputZip = "training-output-zip"
	TrainingRunId     = "training-run-id"
)

type TrainingZipNameConfig struct {
	Name       string
	Version    string
	CommitID   string
	RandomUUID *string
}

func ProduceTrainingZipName(templateName string, conf *TrainingZipNameConfig) (string, error) {
	tmpl, err := template.New("training result name").Parse(templateName)
	if err != nil {
		return "", err
	}

	if conf.RandomUUID == nil {
		uuidString := uuid.New()
		conf.RandomUUID = &uuidString
	}

	var buff bytes.Buffer
	if err := tmpl.Execute(&buff, conf); err != nil {
		return "", err
	}

	return buff.String(), nil
}
