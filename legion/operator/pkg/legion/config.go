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
	"fmt"
	"os"

	"github.com/pkg/errors"
)

var (
	OperatorConf OperatorConfig
)

type BuilderConfig struct {
	RepositoryURL         string
	PodName               string
	DockerRegistry        string
	SharedDirPath         string
	Reference             string
	ResultImagePrefix     string
	BuilderServiceAccount string
	Namespace             string
	Model                 ModelConfig
	GitSSHKeyPath         string
}

type ModelConfig struct {
	FilePath string
	Command  string
}

func NewBuilderConfig() BuilderConfig {
	return BuilderConfig{
		RepositoryURL:         envNotEmpty("REPOSITORY_URL"),
		PodName:               envNotEmpty("POD_NAME"),
		DockerRegistry:        envNotEmpty("DOCKER_REGISTRY"),
		SharedDirPath:         envNotEmpty("SHARED_DIR_PATH"),
		Reference:             envNotEmpty("BRANCH"),
		ResultImagePrefix:     envNotEmpty("RESULT_IMAGE_PREFIX"),
		BuilderServiceAccount: envNotEmpty("BUILDER_SERVICE_ACCOUNT"),
		Namespace:             envNotEmpty("NAMESPACE"),
		GitSSHKeyPath:         envNotEmpty("GIT_SSH_KEY_PATH"),
		Model: ModelConfig{
			FilePath: envNotEmpty("MODEL_FILE"),
			Command:  envNotEmpty("MODEL_COMMAND"),
		},
	}
}

type OperatorConfig struct {
	BuilderImage           string
	MetricHost             string
	MetricPort             string
	MetricEnabled          string
	PythonToolchainImage   string
	BuildImagePrefix       string
	DockerRegistry         string
	DockerRegistryUser     string
	DockerRegistryPassword string
}

func NewOperatorConfig() OperatorConfig {
	return OperatorConfig{
		BuilderImage:           envNotEmpty("BUILDER_IMAGE"),
		MetricHost:             envNotEmpty("METRICS_HOST"),
		MetricPort:             envNotEmpty("METRICS_PORT"),
		MetricEnabled:          envNotEmpty("MODEL_TRAIN_METRICS_ENABLED"),
		PythonToolchainImage:   envNotEmpty("PYTHON_TOOLCHAIN_IMAGE"),
		BuildImagePrefix:       envNotEmpty("BUILD_IMAGE_PREFIX"),
		DockerRegistry:         envNotEmpty("DOCKER_REGISTRY"),
		DockerRegistryUser:     envNotEmpty("DOCKER_REGISTRY_USER"),
		DockerRegistryPassword: envNotEmpty("DOCKER_REGISTRY_PASSWORD"),
	}
}

func envNotEmpty(envName string) (value string) {
	envValue, present := os.LookupEnv(envName)

	if present {
		return envValue
	}

	panic(errors.New(fmt.Sprintf("The environment variable %s must be set", envName)))
}
