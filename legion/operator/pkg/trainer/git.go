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

package trainer

import (
	"encoding/base64"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	"golang.org/x/crypto/ssh"
	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/config"
	"gopkg.in/src-d/go-git.v4/plumbing"
	"gopkg.in/src-d/go-git.v4/plumbing/transport"
	gogitssh "gopkg.in/src-d/go-git.v4/plumbing/transport/ssh"
	"io"
	"io/ioutil"
	"os"
)

const (
	publicHostKeyFile = "known_hosts"
)

var (
	// Refspec syntax is here https://git-scm.com/book/en/v2/Git-Internals-The-Refspec
	defaultRefSpec = []config.RefSpec{
		"+refs/pull/*:refs/remotes/origin/pr/*",
		"+refs/heads/*:refs/remotes/origin/*",
	}
)

// Clone repository and checkout user specific reference
// Return commit id
func (mt *ModelTrainer) cloneUserRepo(
	k8sTraining *training.K8sTrainer, cloneDir string) (string, error) {
	vcsConn := k8sTraining.VCS

	decodedPublicHostKey, err := base64.StdEncoding.DecodeString(vcsConn.Spec.PublicKey)
	if err != nil {
		return "", err
	}

	err = ioutil.WriteFile(publicHostKeyFile, decodedPublicHostKey, 0600)
	if err != nil {
		return "", err
	}

	decodedKeySecret, err := base64.StdEncoding.DecodeString(vcsConn.Spec.KeySecret)
	if err != nil {
		return "", err
	}

	gitAuth, err := getSSHKeyAuth(decodedKeySecret, publicHostKeyFile)
	if err != nil {
		return "", err
	}

	_ = os.RemoveAll(cloneDir)

	repository, err := git.PlainClone(cloneDir, false, &git.CloneOptions{
		URL:      vcsConn.Spec.URI,
		Progress: os.Stdout,
		Auth:     gitAuth,
	})
	if err != nil {
		mt.log.Error(err, "Cloning git repository")
		return "", err
	}

	// Fetch additional references. For example, github pull request references
	err = repository.Fetch(&git.FetchOptions{
		RefSpecs: defaultRefSpec,
		Progress: os.Stdout,
		Auth:     gitAuth,
		Tags:     git.AllTags,
	})
	if err != nil {
		mt.log.Info("Fetching additional references failed")
	}

	referenceName := k8sTraining.ModelTraining.Spec.Reference
	hash, err := mt.tryGetHash(repository, referenceName)
	if err != nil {
		mt.log.Error(err, "Determine full reference name")

		return "", err
	}

	w, err := repository.Worktree()
	if err != nil {
		return "", err
	}

	err = w.Checkout(&git.CheckoutOptions{
		Hash: hash,
	})
	if err != nil {
		mt.log.Error(err, fmt.Sprintf("Checkout reference: %s", referenceName))
	}

	return hash.String(), err
}

func getSSHKeyAuth(sshKey []byte, knownHostPath string) (transport.AuthMethod, error) {
	var auth transport.AuthMethod

	signer, err := ssh.ParsePrivateKey(sshKey)
	if err != nil {
		return auth, err
	}

	keyCallback, err := gogitssh.NewKnownHostsCallback(knownHostPath)
	if err != nil {
		return nil, err
	}

	auth = &gogitssh.PublicKeys{
		User:   "git",
		Signer: signer,
		HostKeyCallbackHelper: gogitssh.HostKeyCallbackHelper{
			HostKeyCallback: keyCallback,
		},
	} //+safeToCommit

	return auth, nil
}

// User reference can be short reference(for example: develop),
// full reference(for example: refs/remotes/origin/develop) or just a hash commit.
// Determine in the following order:
//   * full reference
//   * tag
//   * branch
//   * commit hash
//   * short commit hash
// Return error if not one of the options did not fit
func (mt *ModelTrainer) tryGetHash(repository *git.Repository, reference string) (plumbing.Hash, error) {
	commitHash := plumbing.Hash{}

	ref, err := repository.Reference(plumbing.ReferenceName(reference), true)
	if err == nil {
		mt.log.Info(fmt.Sprintf("'%s' is a reference", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/tags/%s", reference)), true)
	if err == nil {
		mt.log.Info(fmt.Sprintf("'%s' is a tag", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/remotes/%s", reference)), true)
	if err == nil {
		mt.log.Info(fmt.Sprintf("'%s' is a branch", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/remotes/origin/%s", reference)), true)
	if err == nil {
		mt.log.Info(fmt.Sprintf("'%s' is a branch", reference))
		return ref.Hash(), nil
	}

	commit, err := repository.CommitObject(plumbing.NewHash(reference))
	if err == nil {
		mt.log.Info(fmt.Sprintf("'%s' is a commit hash", reference))
		return commit.Hash, nil
	}

	commits, err := repository.CommitObjects()
	if err != nil {
		return commitHash, err
	}

	for {
		commit, err := commits.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return commitHash, err
		}

		if commit.Hash.String()[:len(reference)] == reference {
			mt.log.Info(fmt.Sprintf("'%s' is a short commit hash", reference))
			return commit.Hash, nil
		}
	}

	return commitHash, fmt.Errorf("can't find '%s' refs in git repository", reference)
}
