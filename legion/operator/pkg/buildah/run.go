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

// Read more about run command
// https://github.com/containers/buildah/blob/master/docs/buildah-run.md
func RunCmd(args ...RunArg) error {
	argsList := &RunArgs{}
	for _, option := range args {
		option(argsList)
	}

	params := []string{"run"}

	if len(argsList.User) != 0 {
		params = append(params, "--user", argsList.User)
	}

	if argsList.Volume != nil {
		params = append(params, "--volume", *argsList.Volume)
	}

	if argsList.Network != nil {
		params = append(params, "--net", *argsList.Network)
	}

	params = append(params, "--cap-add", "CAP_SYS_ADMIN")
	//params = append(params, "--security-opt", "seccomp=unconfined")
	//params = append(params, "--isolation", "oci")
	params = append(params, "--storage-driver", "vfs")
	params = append(params, "-v", "/sys:/sys:rw")
	//params = append(params, "--no-pivot")
	//params = append(params,
	//"--security-opt", "label=disable",
	//"--security-opt", "seccomp=unconfined",
	//"-v", "/dev/fuse:/dev/fuse:rw")
	// --security-opt label=disable --security-opt seccomp=unconfined --device /dev/fuse:rw

	params = append(params, argsList.ContainerName, "--")
	params = append(params, argsList.Commands...)

	cmd := exec.Command("buildah", params...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

type RunArgs struct {
	ContainerName string
	User          string
	Commands      []string
	Volume        *string
	Network       *string
}

type RunArg func(*RunArgs)

func ContainerNameRunArg(containerName string) RunArg {
	return func(args *RunArgs) {
		args.ContainerName = containerName
	}
}

func UserRunArg(user string) RunArg {
	return func(args *RunArgs) {
		args.User = user
	}
}

func CommandRunArg(commands ...string) RunArg {
	return func(args *RunArgs) {
		args.Commands = commands
	}
}

func VolumeRunArg(src, dst string) RunArg {
	return func(args *RunArgs) {
		volume := fmt.Sprintf("%s:%s:z", src, dst)
		args.Volume = &volume
	}
}

func NetworkRunArg(network string) RunArg {
	return func(args *RunArgs) {
		args.Network = &network
	}
}
