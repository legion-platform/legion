package utils

import (
	"bytes"
	"errors"
	"fmt"
	"os/exec"
	"regexp"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const PublicSshKeyName = "ssh_known_hosts"

var (
	SshUrlRegexp = regexp.MustCompile(`(?P<User>\w+)@(?P<Host>[\w.]+):.*`)
	logSsh       = logf.Log.WithName("ssh")
)

// TODO: Need to find a better solution.
// url.Parse can't find a host
// url.Parse with git+ssh://url does not evaluate a valid host.
func extractHost(gitUrl string) (string, error) {
	// [0] - full url, [1] - user, [2] - host
	gitHost := SshUrlRegexp.FindStringSubmatch(gitUrl)[2]

	if gitHost == "" {
		return "", errors.New(fmt.Sprintf("Can't extract host from %s url", gitUrl))
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
