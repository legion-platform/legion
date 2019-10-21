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
	"encoding/base64"
	"errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	uuid "github.com/nu7hatch/gouuid"
	"go.uber.org/multierr"
)

const (
	ErrorMessageTemplate           = "%s: %s"
	EmptyURIErrorMessage           = "the uri parameter is empty"
	ValidationConnErrorMessage     = "Validation of connection is failed"
	UnknownTypeErrorMessage        = "unknown type: %s. Supported types: %s"
	DockerTypePasswordErrorMessage = "docker type requires the password parameter" //nolint
	DockerTypeUsernameErrorMessage = "docker type requires the username parameter"
	GitTypePublicKeyErrorMessage   = "git type requires that publicKey parameter must be encoded" +
		" in base64 format, error message: %s"
	GitTypeKeySecretErrorMessage = "git type requires that keySecret parameter must be encoded" +
		" in base64 format, error message: %s"
	GcsTypeRegionErrorMessage                = "gcs type requires that region must be non-empty"
	GcsTypeRoleAndKeySecretEmptyErrorMessage = "gcs type requires that either role or keySecret parameter" +
		" must be non-empty"
	AzureBlobTypeKeySecretEmptyErrorMessage = "azureblob type requires that keySecret parameter contains" +
		"HTTP endpoint with SAS Token"
	S3TypeRegionErrorMessage                = "s3 type requires that region must be non-empty"
	S3TypeRoleAndKeySecretEmptyErrorMessage = "s3 type requires that either role or keySecret parameter" +
		" must be non-empty"
	defaultIDTemplate = "%s-%s"
)

type ConnValidator struct {
}

// Currently validator does not need any arguments
func NewConnValidator() *ConnValidator {
	return &ConnValidator{}
}

func (cv *ConnValidator) ValidatesAndSetDefaults(conn *connection.Connection) (err error) {
	if len(conn.ID) == 0 {
		u4, uuidErr := uuid.NewV4()
		if uuidErr != nil {
			err = multierr.Append(err, uuidErr)
		} else {
			conn.ID = fmt.Sprintf(defaultIDTemplate, conn.Spec.Type, u4.String())
			logC.Info("Connection id is empty. Generate a default value", "id", conn.ID)
		}
	}

	if len(conn.Spec.URI) == 0 {
		err = multierr.Append(err, errors.New(EmptyURIErrorMessage))
	}

	switch conn.Spec.Type {
	case connection.GITType:
		err = multierr.Append(err, validateGitType(conn))
	case connection.S3Type:
		err = multierr.Append(err, validateS3Type(conn))
	case connection.GcsType:
		err = multierr.Append(err, validateGcsType(conn))
	case connection.AzureBlobType:
		err = multierr.Append(err, validateAzureBlobType(conn))
	case connection.DockerType:
		err = multierr.Append(err, validateDockerType(conn))
	default:
		err = multierr.Append(err, fmt.Errorf(UnknownTypeErrorMessage, conn.Spec.Type, connection.AllConnectionTypes))
	}

	if err != nil {
		return fmt.Errorf(ErrorMessageTemplate, ValidationConnErrorMessage, err.Error())
	}

	return err
}

func validateS3Type(conn *connection.Connection) (err error) {
	if len(conn.Spec.Region) == 0 {
		err = multierr.Append(err, errors.New(S3TypeRegionErrorMessage))
	}

	if len(conn.Spec.Role) == 0 && len(conn.Spec.KeySecret) == 0 {
		err = multierr.Append(err, errors.New(S3TypeRoleAndKeySecretEmptyErrorMessage))
	}

	if len(conn.Spec.Role) != 0 && len(conn.Spec.KeySecret) != 0 {
		err = multierr.Append(err, errors.New(S3TypeRoleAndKeySecretEmptyErrorMessage))
	}

	return
}

func validateGcsType(conn *connection.Connection) (err error) {
	if len(conn.Spec.Region) == 0 {
		err = multierr.Append(err, errors.New(GcsTypeRegionErrorMessage))
	}

	if len(conn.Spec.Role) == 0 && len(conn.Spec.KeySecret) == 0 {
		err = multierr.Append(err, errors.New(GcsTypeRoleAndKeySecretEmptyErrorMessage))
	}

	if len(conn.Spec.Role) != 0 && len(conn.Spec.KeySecret) != 0 {
		err = multierr.Append(err, errors.New(GcsTypeRoleAndKeySecretEmptyErrorMessage))
	}

	return
}

func validateAzureBlobType(conn *connection.Connection) (err error) {
	if len(conn.Spec.KeySecret) == 0 {
		err = multierr.Append(err, errors.New(AzureBlobTypeKeySecretEmptyErrorMessage))
	}

	return
}

func validateDockerType(conn *connection.Connection) (err error) {
	if len(conn.Spec.Password) == 0 {
		err = multierr.Append(err, errors.New(DockerTypePasswordErrorMessage))
	}

	if len(conn.Spec.Username) == 0 {
		err = multierr.Append(err, errors.New(DockerTypeUsernameErrorMessage))
	}

	return
}

func validateGitType(conn *connection.Connection) (err error) {
	if len(conn.Spec.KeySecret) != 0 {
		_, base64err := base64.StdEncoding.DecodeString(conn.Spec.KeySecret)

		if base64err != nil {
			err = multierr.Append(base64err, fmt.Errorf(GitTypeKeySecretErrorMessage, base64err.Error()))
		}
	}

	if len(conn.Spec.PublicKey) != 0 {
		_, base64err := base64.StdEncoding.DecodeString(conn.Spec.PublicKey)

		if base64err != nil {
			err = multierr.Append(base64err, fmt.Errorf(GitTypePublicKeyErrorMessage, base64err.Error()))
		}
	}

	return err
}
