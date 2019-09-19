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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	conn_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/storage/kubernetes"
	mp_storage "github.com/legion-platform/legion/legion/operator/pkg/storage/packaging"
	uuid "github.com/nu7hatch/gouuid"
	"github.com/xeipuuv/gojsonschema"
	"go.uber.org/multierr"
)

const (
	ValidationMpErrorMessage             = "Validation of model packaging is failed"
	TrainingIdOrArtifactNameErrorMessage = "you should specify artifactName"
	ArgumentValidationErrorMessage       = "argument validation is failed: %s"
	EmptyIntegrationNameErrorMessage     = "integration name must be nonempty"
	TargetNotFoundErrorMessage           = "cannot find %s target in packaging integration %s"
	NotValidConnTypeErrorMessage         = "%s target has not valid connection type %s for packaging integration %s"
	defaultIdTemplate                    = "%s-%s-%s"
)

var (
	defaultMemoryLimit        = "2028Mi"
	defaultCpuLimit           = "2000m"
	defaultMemoryRequests     = "1024Mi"
	defaultCpuRequests        = "1000m"
	DefaultPackagingResources = &v1alpha1.ResourceRequirements{
		Limits: &v1alpha1.ResourceList{
			Cpu:    &defaultCpuLimit,
			Memory: &defaultMemoryLimit,
		},
		Requests: &v1alpha1.ResourceList{
			Cpu:    &defaultCpuRequests,
			Memory: &defaultMemoryRequests,
		},
	}
)

type MpValidator struct {
	storage     mp_storage.Storage
	connStorage conn_storage.Storage
}

func NewMpValidator(storage mp_storage.Storage, connStorage conn_storage.Storage) *MpValidator {
	return &MpValidator{
		storage:     storage,
		connStorage: connStorage,
	}
}

func (mpv *MpValidator) ValidateAndSetDefaults(mp *packaging.ModelPackaging) (err error) {
	err = multierr.Append(err, mpv.validateMainParameters(mp))

	if len(mp.Spec.IntegrationName) == 0 {
		err = multierr.Append(err, errors.New(EmptyIntegrationNameErrorMessage))
	} else {
		if pi, k8sErr := mpv.storage.GetPackagingIntegration(mp.Spec.IntegrationName); k8sErr != nil {
			err = multierr.Append(err, k8sErr)
		} else {
			err = multierr.Append(err, mpv.validateArguments(pi, mp))

			err = multierr.Append(err, mpv.validateTargets(pi, mp))
		}

	}

	if err != nil {
		return fmt.Errorf("%s: %s", ValidationMpErrorMessage, err.Error())
	}

	return nil
}

func (mpv *MpValidator) validateMainParameters(mp *packaging.ModelPackaging) (err error) {
	if len(mp.Id) == 0 {
		u4, uuidErr := uuid.NewV4()
		if uuidErr != nil {
			err = multierr.Append(err, uuidErr)
		} else {
			mp.Id = fmt.Sprintf(defaultIdTemplate, mp.Spec.ArtifactName, mp.Spec.IntegrationName, u4.String())
			logMP.Info("Model packaging id is empty. Generate a default value", "id", mp.Id)
		}
	}

	if len(mp.Spec.Image) == 0 {
		packagingIntegration, k8sErr := mpv.storage.GetPackagingIntegration(mp.Spec.IntegrationName)
		if k8sErr != nil {
			err = multierr.Append(err, k8sErr)
		} else {
			mp.Spec.Image = packagingIntegration.Spec.DefaultImage
			logMP.Info("Model packaging id is empty. Set a packaging integration image",
				"id", mp.Id, "image", mp.Spec.Image)
		}
	}

	if len(mp.Spec.ArtifactName) == 0 {
		err = multierr.Append(err, errors.New(TrainingIdOrArtifactNameErrorMessage))
	}

	if mp.Spec.Resources == nil {
		logMP.Info("Packaging resource parameter is nil. Set the default value",
			"name", mp.Id, "resources", DefaultPackagingResources)
		mp.Spec.Resources = DefaultPackagingResources
	} else {
		_, resValidationErr := kubernetes.ConvertLegionResourcesToK8s(mp.Spec.Resources)
		err = multierr.Append(err, resValidationErr)
	}

	return
}

func (mpv *MpValidator) validateArguments(pi *packaging.PackagingIntegration, mp *packaging.ModelPackaging) error {
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

	schemaLoader := gojsonschema.NewGoLoader(jsonSchema)
	data := make(map[string]interface{})
	if mp.Spec.Arguments != nil {
		data = mp.Spec.Arguments
	}
	dataLoader := gojsonschema.NewGoLoader(data)
	result, err := gojsonschema.Validate(schemaLoader, dataLoader)
	if err != nil {
		return err
	}

	if result.Valid() {
		return nil
	} else {
		return fmt.Errorf(ArgumentValidationErrorMessage, result.Errors())
	}
}

func (mpv *MpValidator) validateTargets(pi *packaging.PackagingIntegration, mp *packaging.ModelPackaging) (err error) {
	requiredTargets := make(map[string]interface{})
	allTargets := make(map[string]v1alpha1.TargetSchema)

	for _, target := range pi.Spec.Schema.Targets {
		allTargets[target.Name] = target

		if target.Required {
			requiredTargets[target.Name] = nil
		}
	}

	for _, target := range mp.Spec.Targets {
		if _, ok := requiredTargets[target.Name]; ok {
			delete(requiredTargets, target.Name)
		}

		if targetSchema, ok := allTargets[target.Name]; !ok {
			err = multierr.Append(err, fmt.Errorf(TargetNotFoundErrorMessage, target.Name, pi.Id))
		} else {
			if conn, k8sErr := mpv.connStorage.GetConnection(target.ConnectionName); k8sErr != nil {
				err = multierr.Append(err, k8sErr)
			} else {
				isValidConnectionType := false

				for _, connType := range targetSchema.ConnectionTypes {
					if v1alpha1.ConnectionType(connType) == conn.Spec.Type {
						isValidConnectionType = true
						break
					}
				}

				if !isValidConnectionType {
					err = multierr.Append(err, fmt.Errorf(NotValidConnTypeErrorMessage, target.Name, conn.Spec.Type, pi.Id))
				}
			}
		}
	}

	if len(requiredTargets) != 0 {
		requiredTargetsList := make([]string, 0)
		for targetName := range requiredTargets {
			requiredTargetsList = append(requiredTargetsList, targetName)
		}

		err = multierr.Append(err, fmt.Errorf("%s are required targets", requiredTargetsList))
	}

	return
}
