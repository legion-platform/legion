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
	"strings"
)

const (
	PythonToolchainName  = "python"
	JupiterToolchainName = "jupyter"
)

func GetToolchainImage(toolchainName string) (image string, err error) {
	switch toolchainName {
	case PythonToolchainName:
		return viper.GetString(PythonToolchainImage), nil
	case JupiterToolchainName:
		return viper.GetString(PythonToolchainImage), nil
	}

	return "", errors.New(fmt.Sprintf("Can't find %s toolchain", toolchainName))
}

func GenerateModelCommand(workDir string, toolchainName string, entrypoint string,
	args []string) (string, error) {
	var pythonCommand strings.Builder
	if len(workDir) != 0 {
		pythonCommand.WriteString(fmt.Sprintf("cd %s && ", fmt.Sprintf(workDir)))
	}

	switch toolchainName {
	case PythonToolchainName:
		pythonCommand.WriteString(fmt.Sprintf("python3 %s", entrypoint))

		for _, arg := range args {
			pythonCommand.WriteString(" " + arg)
		}
	case JupiterToolchainName:
		// TODO: need to think about jupyter parameters
		pythonCommand.WriteString(fmt.Sprintf("jupyter nbconvert --execute %s", entrypoint))
	default:
		return "", errors.New(fmt.Sprintf("Can't find %s toolchain", toolchainName))
	}

	return pythonCommand.String(), nil
}
