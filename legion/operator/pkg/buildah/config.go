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

package buildah

import (
	"fmt"
	"os"
	"os/exec"
)

// Read more about config buildah parameters
// https://github.com/containers/buildah/blob/master/docs/buildah-config.md
func ConfigCmd(args ...ConfigArg) error {
	argsList := &ConfigArgs{}
	for _, option := range args {
		option(argsList)
	}

	params := []string{"config"}

	for _, env := range argsList.Envs {
		params = append(params, "--env", env)
	}

	if argsList.WorkingDir != nil {
		params = append(params, "--workingdir", *argsList.WorkingDir)
	}

	params = append(params, argsList.ContainerName)

	cmd := exec.Command("buildah", params...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

type ConfigArgs struct {
	ContainerName string
	Envs          []string
	WorkingDir    *string
}

type ConfigArg func(*ConfigArgs)

func ContainerNameConfigArg(containerName string) ConfigArg {
	return func(args *ConfigArgs) {
		args.ContainerName = containerName
	}
}

func EnvsConfigArg(envs map[string]string) ConfigArg {
	return func(args *ConfigArgs) {
		for k, v := range envs {
			args.Envs = append(args.Envs, fmt.Sprintf("%s=%s", k, v))
		}
	}
}

func WorkingDirConfigArg(workingDir string) ConfigArg {
	return func(args *ConfigArgs) {
		args.WorkingDir = &workingDir
	}
}
