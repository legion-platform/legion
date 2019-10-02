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

package connection

import (
	"bytes"
	"fmt"
	"os/exec"
	"regexp"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const PublicSshKeyName = "ssh_known_hosts"

var (
	SshUrlRegexp = regexp.MustCompile(`(?P<User>.+)@(?P<Host>[\w.]+)[/:].*`)
	logSsh       = logf.Log.WithName("ssh")
)

// TODO: Need to find a better solution.
// url.Parse can't find a host
// url.Parse with git+ssh://url does not evaluate a valid host.
func extractHost(gitUrl string) (string, error) {
	// [0] - full url, [1] - user, [2] - host
	gitHost := SshUrlRegexp.FindStringSubmatch(gitUrl)[2]

	if gitHost == "" {
		return "", fmt.Errorf("can't extract host from %s url", gitUrl)
	}

	return gitHost, nil
}

// TODO: Need to find a better solution.
// The best way is use standard library.
func EvaluatePublicKey(sshUrl string) (string, error) {
	sshHost, err := extractHost(sshUrl)
	if err != nil {
		return "", err
	}

	cmd := exec.Command("ssh-keyscan", sshHost)

	var outBuf bytes.Buffer
	var errBuf bytes.Buffer
	cmd.Stdout = &outBuf
	cmd.Stderr = &errBuf

	err = cmd.Run()

	if err != nil {
		logSsh.Error(err, fmt.Sprintf("Stderr: %s", errBuf.String()))
		return "", err
	}

	return outBuf.String(), nil
}
