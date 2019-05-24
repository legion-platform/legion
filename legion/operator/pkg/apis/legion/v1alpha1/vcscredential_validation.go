package v1alpha1

import (
	"encoding/base64"
	"errors"
	"go.uber.org/multierr"
)

const (
	emptyUriErrorMessage = "the uri parameter is empty"
)

func (vcs *VCSCredential) ValidatesAndSetDefaults() (err error) {
	if len(vcs.Spec.Credential) != 0 {
		_, base64err := base64.StdEncoding.DecodeString(vcs.Spec.Credential)

		if base64err != nil {
			err = multierr.Append(base64err, err)
		}
	}

	if len(vcs.Spec.PublicKey) != 0 {
		_, base64err := base64.StdEncoding.DecodeString(vcs.Spec.PublicKey)

		if base64err != nil {
			err = multierr.Append(base64err, err)
		}
	}

	if len(vcs.Spec.Uri) == 0 {
		err = multierr.Append(err, errors.New(emptyUriErrorMessage))
	}

	return
}
