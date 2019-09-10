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

package training

import (
	"errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	uuid "github.com/nu7hatch/gouuid"
	"go.uber.org/multierr"
)

const (
	ValidationTiErrorMessage      = "Validation of toolchain integration is failed"
	EmptyEntrypointErrorMessage   = "entrypoint must be no empty"
	EmptyDefaultImageErrorMessage = "defaultImage must be no empty"
)

type TiValidator struct {
}

func NewTiValidator() *TiValidator {
	return &TiValidator{}
}

func (tiv *TiValidator) ValidatesAndSetDefaults(ti *training.ToolchainIntegration) (err error) {
	if len(ti.Id) == 0 {
		u4, uuidErr := uuid.NewV4()
		if uuidErr != nil {
			err = multierr.Append(err, uuidErr)
		} else {
			ti.Id = u4.String()
			logTI.Info("Toolchain integration id is empty. Generate a default value", "id", ti.Id)
		}

	}

	if len(ti.Spec.Entrypoint) == 0 {
		err = multierr.Append(err, errors.New(EmptyEntrypointErrorMessage))
	}

	if len(ti.Spec.DefaultImage) == 0 {
		err = multierr.Append(err, errors.New(EmptyDefaultImageErrorMessage))
	}

	if err != nil {
		return fmt.Errorf("%s: %s", ValidationTiErrorMessage, err.Error())
	}

	return
}
