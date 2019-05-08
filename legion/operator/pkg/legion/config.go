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
	"github.com/pkg/errors"
	"github.com/spf13/viper"
)

const (
	RepositoryURL          = "REPOSITORY_URL"
	PodName                = "POD_NAME"
	DockerRegistry         = "DOCKER_REGISTRY"
	SharedDirPath          = "SHARED_DIR_PATH"
	Reference              = "REFERENCE"
	ImagePrefix            = "BUILD_IMAGE_PREFIX"
	Namespace              = "NAMESPACE"
	GitSSHKeyPath          = "GIT_SSH_KEY_PATH"
	ModelFile              = "MODEL_FILE"
	ModelCommand           = "MODEL_COMMAND"
	BuilderImage           = "BUILDER_IMAGE"
	MetricHost             = "METRICS_HOST"
	MetricPort             = "METRICS_PORT"
	MetricEnabled          = "MODEL_TRAIN_METRICS_ENABLED"
	PythonToolchainImage   = "PYTHON_TOOLCHAIN_IMAGE"
	DockerRegistryUser     = "DOCKER_REGISTRY_USER"
	DockerRegistryPassword = "DOCKER_REGISTRY_PASSWORD"
	JwtSecret              = "JWT_SECRET"
	JwtTtlMinutes          = "JWT_TTL_MINUTES"
	JwtMaxTtlMinutes       = "JWT_MAX_TTL_MINUTES"
	JwtExpDatetime         = "JWT_EXP_DATETIME"
	TemplateFolder         = "TEMPLATE_FOLDER"
	BuilderServiceAccount  = "BUILDER_SERVICE_ACCOUNT"
)

// TODO:
// It is just a first attempt of using viper
// Later we must to add default values and reading from a config file which mounts from k8s config map.
func SetUpBuilderConfig() {
	setNotEmptyParam(RepositoryURL)
	setNotEmptyParam(PodName)
	setNotEmptyParam(DockerRegistry)
	setNotEmptyParam(SharedDirPath)
	setNotEmptyParam(Reference)
	setNotEmptyParam(ImagePrefix)
	setNotEmptyParam(Namespace)
	setNotEmptyParam(GitSSHKeyPath)
	setNotEmptyParam(ModelFile)
	setNotEmptyParam(ModelCommand)
}

func SetUpOperatorConfig() {
	setNotEmptyParam(BuilderImage)
	setNotEmptyParam(MetricHost)
	setNotEmptyParam(MetricPort)
	setNotEmptyParam(MetricEnabled)
	setNotEmptyParam(PythonToolchainImage)
	setNotEmptyParam(DockerRegistry)

	viper.SetDefault(ImagePrefix, "legion")
	panicIfError(viper.BindEnv(ImagePrefix))

	viper.SetDefault(BuilderServiceAccount, "legion-builder")
	panicIfError(viper.BindEnv(BuilderServiceAccount))

	panicIfError(viper.BindEnv(DockerRegistryUser))
	panicIfError(viper.BindEnv(DockerRegistryPassword))
}

func SetUpEDIConfig() {
	viper.SetDefault(Namespace, "default")
	panicIfError(viper.BindEnv(Namespace))

	viper.SetDefault(JwtTtlMinutes, 120)
	panicIfError(viper.BindEnv(JwtTtlMinutes))

	viper.SetDefault(JwtSecret, "")
	panicIfError(viper.BindEnv(JwtSecret))

	viper.SetDefault(JwtMaxTtlMinutes, 259200)
	panicIfError(viper.BindEnv(JwtMaxTtlMinutes))

	viper.SetDefault(JwtExpDatetime, "")
	panicIfError(viper.BindEnv(JwtExpDatetime))

	viper.SetDefault(TemplateFolder, "legion/operator/templates")
	panicIfError(viper.BindEnv(TemplateFolder))
}

func setNotEmptyParam(paramName string) {
	panicIfError(viper.BindEnv(paramName))

	if !viper.IsSet(paramName) {
		panic(errors.New(fmt.Sprintf("The environment variable %s must be set", paramName)))
	}
}

func panicIfError(err error) {
	if err != nil {
		panic(err)
	}
}
