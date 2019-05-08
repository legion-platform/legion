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

package utils

import (
	"encoding/json"
	"fmt"
	"github.com/docker/distribution/manifest/schema1"
	"github.com/heroku/docker-registry-client/registry"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/pkg/errors"
	"github.com/spf13/viper"
	"io/ioutil"
	"net/http"
	"regexp"
)

var (
	dockerImageRegexp = regexp.MustCompile(`(.*?)/([\w\-/]+):([\-.\w]+)`)
)

type imageAttrs struct {
	host string
	name string
	tag  string
}

type LabelExtractor func(image string) (map[string]string, error)

func parseImage(image string) (*imageAttrs, error) {
	submatch := dockerImageRegexp.FindStringSubmatch(image)
	host, name, tag := submatch[1], submatch[2], submatch[3]

	fmt.Println(fmt.Sprintf("Extract [host=%s,name=%s,tag=%s] from %s image", host, name, tag, image))

	if host == "" {
		return nil, errors.New("Host is empty")
	}
	if name == "" {
		return nil, errors.New("Name is empty")
	}
	if tag == "" {
		return nil, errors.New("Tag is empty")
	}

	return &imageAttrs{host: fmt.Sprintf("https://%s", host), name: name, tag: tag}, nil
}

func ExtractDockerLabels(image string) (labels map[string]string, err error) {
	imageAttrs, err := parseImage(image)
	if err != nil {
		return nil, err
	}

	hub, err := registry.New(
		imageAttrs.host,
		viper.GetString(legion.DockerRegistryUser),
		viper.GetString(legion.DockerRegistryPassword),
	)

	if err != nil {
		return nil, err
	}

	url := fmt.Sprintf("%s/v2/%s/manifests/%s", imageAttrs.host, imageAttrs.name, imageAttrs.tag)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", schema1.MediaTypeManifest)
	resp, err := hub.Client.Do(req)
	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	manifest := &schema1.Manifest{}
	err = json.Unmarshal(body, manifest)
	if err != nil {
		return nil, err
	}

	var v1Compatibility struct {
		ContainerConfig struct {
			Labels map[string]string `json:"Labels"`
		} `json:"container_config"`
	}

	err = json.Unmarshal([]byte(manifest.History[0].V1Compatibility), &v1Compatibility)
	if err != nil {
		return nil, err
	}

	return v1Compatibility.ContainerConfig.Labels, nil
}
