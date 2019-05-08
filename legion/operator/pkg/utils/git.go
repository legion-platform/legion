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
	"errors"
	"fmt"
	"golang.org/x/crypto/ssh"
	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/config"
	"gopkg.in/src-d/go-git.v4/plumbing"
	"gopkg.in/src-d/go-git.v4/plumbing/transport"
	gogitssh "gopkg.in/src-d/go-git.v4/plumbing/transport/ssh"
	"io"
	"io/ioutil"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("git")

const (
	GitSSHKeyFileName = "id_rsa"
)

var (
	// Refspec syntax is here https://git-scm.com/book/en/v2/Git-Internals-The-Refspec
	defaultRefSpec = []config.RefSpec{
		"+refs/pull/*:refs/remotes/origin/pr/*",
		"+refs/heads/*:refs/remotes/origin/*",
	}
)

// Clone repository and checkout user specific reference
func CloneUserRepo(cloneDir string, repositoryUrl string, sshKeyPath string, referenceName string) (err error) {
	gitAuth, err := getSshKeyAuth(sshKeyPath)
	if err != nil {
		return
	}

	_ = os.RemoveAll(cloneDir)

	repository, err := git.PlainClone(cloneDir, false, &git.CloneOptions{
		URL:      repositoryUrl,
		Progress: os.Stdout,
		Auth:     gitAuth,
	})
	if err != nil {
		log.Error(err, "Cloning git repository")
		return err
	}

	// Fetch additional references. For example, github pull request references
	err = repository.Fetch(&git.FetchOptions{
		RefSpecs: defaultRefSpec,
		Progress: os.Stdout,
		Auth:     gitAuth,
		Tags:     git.AllTags,
	})
	if err != nil {
		log.Error(err, "Fetching additional references")
		return err
	}

	hash, err := tryGetHash(repository, referenceName)
	if err != nil {
		log.Error(err, "Determine full reference name")
		return err
	}

	w, err := repository.Worktree()
	if err != nil {
		return err
	}

	err = w.Checkout(&git.CheckoutOptions{
		Hash: hash,
	})
	if err != nil {
		log.Error(err, fmt.Sprintf("Checkout reference: %s", referenceName))
	}

	return nil
}

func getSshKeyAuth(sshKeyPath string) (transport.AuthMethod, error) {
	var auth transport.AuthMethod

	sshKey, err := ioutil.ReadFile(sshKeyPath)
	if err != nil {
		return auth, err
	}

	signer, err := ssh.ParsePrivateKey([]byte(sshKey))
	if err != nil {
		return auth, err
	}

	auth = &gogitssh.PublicKeys{User: "git", Signer: signer} //+safeToCommit

	return auth, nil
}

// User reference can be short reference(for example: develop), full reference(for example: refs/remotes/origin/develop) or
// just a hash commit.
// Determine in the following order:
//   * full reference
//   * tag
//   * branch
//   * commit hash
//   * short commit hash
// Return error if not one of the options did not fit
func tryGetHash(repository *git.Repository, reference string) (plumbing.Hash, error) {
	commitHash := plumbing.Hash{}

	ref, err := repository.Reference(plumbing.ReferenceName(reference), true)
	if err == nil {
		log.Info(fmt.Sprintf("'%s' is a reference", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/tags/%s", reference)), true)
	if err == nil {
		log.Info(fmt.Sprintf("'%s' is a tag", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/remotes/%s", reference)), true)
	if err == nil {
		log.Info(fmt.Sprintf("'%s' is a branch", reference))
		return ref.Hash(), nil
	}

	ref, err = repository.Reference(plumbing.ReferenceName(fmt.Sprintf("refs/remotes/origin/%s", reference)), true)
	if err == nil {
		log.Info(fmt.Sprintf("'%s' is a branch", reference))
		return ref.Hash(), nil
	}

	commit, err := repository.CommitObject(plumbing.NewHash(reference))
	if err == nil {
		log.Info(fmt.Sprintf("'%s' is a commit hash", reference))
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
			log.Info(fmt.Sprintf("'%s' is a short commit hash", reference))
			return commit.Hash, nil
		}
	}

	return commitHash, errors.New(fmt.Sprintf("Can't find '%s' refs in git repository", reference))
}
