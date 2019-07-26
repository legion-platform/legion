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
	"os"
	"os/exec"
)

// Read more about from command
// https://github.com/containers/buildah/blob/master/docs/buildah-pull.md
func FromCmd(args ...FromArg) error {
	argsList := &FromArgs{}
	for _, option := range args {
		option(argsList)
	}

	cmd := exec.Command("buildah", "from", "--name", argsList.ContainerName, argsList.BaseImage)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

type FromArgs struct {
	ContainerName string
	BaseImage     string
}

type FromArg func(*FromArgs)

func ContainerNameFromArg(containerName string) FromArg {
	return func(args *FromArgs) {
		args.ContainerName = containerName
	}
}

func BaseImageFromArg(baseImage string) FromArg {
	return func(args *FromArgs) {
		args.BaseImage = baseImage
	}
}
