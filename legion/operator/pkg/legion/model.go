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
	"archive/zip"
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/pkg/errors"
	"io"
	"log"
	"regexp"
	"strings"
)

type Model struct {
	ID      string `json:"model.id"`
	Version string `json:"model.version"`
}

const (
	ManifestFile    = "manifest.json"
	ModelImageKey   = "model-image"
	ModelIDKey      = "model-id"
	ModelVersionKey = "model-version"
	ModelCommitID   = "model-commit-id"
)

var (
	invalidCharsRegexp = regexp.MustCompile("[^a-zA-Z0-9-]")
)

func ExtractModel(modelFile string) (model Model, err error) {
	r, err := zip.OpenReader(modelFile)
	if err != nil {
		log.Fatal(err)
	}
	defer r.Close()

	for _, f := range r.File {
		if f.Name == ManifestFile {
			var rc io.ReadCloser
			rc, err = f.Open()

			if err != nil {
				return
			}
			defer rc.Close()

			var buffer bytes.Buffer
			w_buffer := bufio.NewWriter(&buffer)

			_, err = io.Copy(w_buffer, rc)
			if err != nil {
				return
			}

			err = json.Unmarshal(buffer.Bytes(), &model)
			if err != nil {
				return
			}

			return
		}
	}

	return model, errors.New(fmt.Sprintf("Can't find %s file in the %s model file", ManifestFile, modelFile))
}

func BuildModelImageName(dockerRegistry string, imagePrefix string, modelID string, modelVersion string) string {
	return fmt.Sprintf("%s/%s/%s:%s", dockerRegistry, imagePrefix, modelID, modelVersion)
}

func ConvertTok8sName(modelId string, modelVersion string) string {
	name := fmt.Sprintf("model-%s-%s", modelId, modelVersion)

	invalidDelimiters := []string{" ", "_", "+", "."}
	for _, char := range invalidDelimiters {
		name = strings.Replace(name, char, "-", -1)
	}

	return invalidCharsRegexp.ReplaceAllString(name, "")
}
