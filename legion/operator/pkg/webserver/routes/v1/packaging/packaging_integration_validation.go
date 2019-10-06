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

package packaging

import (
	"errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	"github.com/xeipuuv/gojsonschema"
	"go.uber.org/multierr"
)

const (
	ValidationPiErrorMessage               = "Validation of packaging integration is failed"
	EmptyIDErrorMessage                    = "id must be nonempty"
	EmptyEntrypointErrorMessage            = "entrypoint must be nonempty"
	EmptyDefaultImageErrorMessage          = "default image must be nonempty"
	TargetEmptyConnectionTypesErrorMessage = "%s target must have at least one connection type"
	TargetEmptyNameErrorMessage            = "one of target has empty name"
	TargetUnknownConnTypeErrorMessage      = "%s target have unknown connection type: %s"
	NotValidJSONSchemaErrorMessage         = "arguments have not valid json schema: %s"
	errorMessageTemplate                   = "%s: %s"
)

// Packaging Integration validator
type PiValidator struct {
}

// Currently validator does not need any arguments
func NewPiValidator() *PiValidator {
	return &PiValidator{}
}

func (mpv *PiValidator) validateArgumentsSchema(pi *packaging.PackagingIntegration) error {
	required := make([]string, 0)
	if pi.Spec.Schema.Arguments.Required != nil {
		required = pi.Spec.Schema.Arguments.Required
	}

	properties := make(map[string]map[string]interface{})
	if pi.Spec.Schema.Arguments.Properties != nil {
		for _, prop := range pi.Spec.Schema.Arguments.Properties {
			params := make(map[string]interface{})
			for _, param := range prop.Parameters {
				params[param.Name] = param.Value
			}

			properties[prop.Name] = params
		}
	}

	jsonSchema := map[string]interface{}{
		"type":                 "object",
		"properties":           properties,
		"required":             required,
		"additionalProperties": false,
	}
	if _, validationErr := gojsonschema.NewSchema(gojsonschema.NewGoLoader(jsonSchema)); validationErr != nil {
		return fmt.Errorf(NotValidJSONSchemaErrorMessage, validationErr.Error())
	}

	return nil
}

func (mpv *PiValidator) validateTargetsSchema(pi *packaging.PackagingIntegration) (err error) {
	for _, target := range pi.Spec.Schema.Targets {
		if len(target.Name) == 0 {
			err = multierr.Append(err, errors.New(TargetEmptyNameErrorMessage))
		} else {
			// If the target has a name, then we validate other target parameters.
			if len(target.ConnectionTypes) == 0 {
				err = multierr.Append(err, fmt.Errorf(TargetEmptyConnectionTypesErrorMessage, target.Name))
			} else {
				for _, targetConnType := range target.ConnectionTypes {
					if _, ok := connection.AllConnectionTypesSet[v1alpha1.ConnectionType(targetConnType)]; !ok {
						err = multierr.Append(err, fmt.Errorf(TargetUnknownConnTypeErrorMessage, target.Name, targetConnType))
					}
				}
			}
		}
	}

	return
}

func (mpv *PiValidator) validateMainParameters(pi *packaging.PackagingIntegration) (err error) {
	if len(pi.ID) == 0 {
		err = multierr.Append(err, errors.New(EmptyIDErrorMessage))
	}

	if len(pi.Spec.Entrypoint) == 0 {
		err = multierr.Append(err, errors.New(EmptyEntrypointErrorMessage))
	}

	if len(pi.Spec.DefaultImage) == 0 {
		err = multierr.Append(err, errors.New(EmptyDefaultImageErrorMessage))
	}

	return
}

func (mpv *PiValidator) ValidateAndSetDefaults(pi *packaging.PackagingIntegration) (err error) {
	err = multierr.Append(err, mpv.validateMainParameters(pi))

	err = multierr.Append(err, mpv.validateTargetsSchema(pi))

	err = multierr.Append(err, mpv.validateArgumentsSchema(pi))

	if err != nil {
		return fmt.Errorf(errorMessageTemplate, ValidationPiErrorMessage, err.Error())
	}

	return nil
}
