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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	mt_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
	uuid "github.com/nu7hatch/gouuid"
	"go.uber.org/multierr"
	"reflect"
)

const (
	mtVcsNotExistsErrorMessage    = "cannot find VCS Credential"
	EmptyModelNameErrorMessage    = "model name must be no empty"
	EmptyModelVersionErrorMessage = "model version must be no empty"
	EmptyVcsNameMessageError      = "VCS name is empty"
	ValidationMtErrorMessage      = "Validation of model training is failed"
	WrongVcsTypeErrorMessage      = "VCS connection must have the GIT type. You pass the connection of %s type"
	WrongVcsReferenceErrorMessage = "you should specify a VCS reference for model training explicitly." +
		" Because %s does not have default reference"
	EmptyDataBindingNameErrorMessage = "you should specify connection name for %d number of data binding"
	EmptyDataBindingPathErrorMessage = "you should specify local path for %d number of data binding"
	WrongDataBindingTypeErrorMessage = "%s data binding has wrong data type. Currently supported the following types" +
		" of connections for data bindings: %v"
	ToolchainEmptyErrorMessage = "toolchain parameter is empty"
	defaultIDTemplate          = "%s-%s-%s"
)

var (
	DefaultArtifactOutputTemplate = "{{ .Name }}-{{ .Version }}-{{ .RandomUUID }}.zip"
	defaultMemoryLimit            = "256Mi"
	defaultCPULimit               = "256m"
	defaultMemoryRequests         = "128Mi"
	defaultCPURequests            = "128m"
	DefaultTrainingResources      = v1alpha1.ResourceRequirements{
		Limits: &v1alpha1.ResourceList{
			CPU:    &defaultCPULimit,
			Memory: &defaultMemoryLimit,
		},
		Requests: &v1alpha1.ResourceList{
			CPU:    &defaultCPURequests,
			Memory: &defaultMemoryRequests,
		},
	}
	DefaultExperimentValue      = "experiment"
	expectedConnectionDataTypes = map[v1alpha1.ConnectionType]bool{
		connection.GcsType: true,
		connection.S3Type:  true,
	}
)

type MtValidator struct {
	mtRepository   mt_repository.Repository
	connRepository conn_repository.Repository
}

func NewMtValidator(mtRepository mt_repository.Repository, connRepository conn_repository.Repository) *MtValidator {
	return &MtValidator{
		mtRepository:   mtRepository,
		connRepository: connRepository,
	}
}

func (mtv *MtValidator) ValidatesAndSetDefaults(mt *training.ModelTraining) (err error) {
	err = multierr.Append(err, mtv.validateMainParams(mt))

	err = multierr.Append(err, mtv.validateVCS(mt))

	err = multierr.Append(err, mtv.validateMtData(mt))

	err = multierr.Append(err, mtv.validateToolchain(mt))

	if err != nil {
		return fmt.Errorf("%s: %s", ValidationMtErrorMessage, err.Error())
	}

	return
}

func (mtv *MtValidator) validateMainParams(mt *training.ModelTraining) (err error) {
	if len(mt.Spec.Model.Name) == 0 {
		err = multierr.Append(err, errors.New(EmptyModelNameErrorMessage))
	}

	if len(mt.Spec.Model.Version) == 0 {
		err = multierr.Append(err, errors.New(EmptyModelVersionErrorMessage))
	}

	if len(mt.ID) == 0 {
		u4, uuidErr := uuid.NewV4()
		if uuidErr != nil {
			err = multierr.Append(err, uuidErr)
		} else {
			mt.ID = fmt.Sprintf(defaultIDTemplate, mt.Spec.Model.Name, mt.Spec.Model.Version, u4.String())
			logMT.Info("Training id is empty. Generate a default value", "id", mt.ID)
		}
	}

	if len(mt.Spec.Model.ArtifactNameTemplate) == 0 {
		logMT.Info("Artifact output template is empty. Set the default value",
			"name", mt.ID, "artifact ame", DefaultArtifactOutputTemplate)
		mt.Spec.Model.ArtifactNameTemplate = DefaultArtifactOutputTemplate
	}

	if mt.Spec.Resources == nil {
		logMT.Info("Training resource parameter is nil. Set the default value",
			"name", mt.ID, "resources", DefaultTrainingResources)
		mt.Spec.Resources = &DefaultTrainingResources
	} else {
		_, resValidationErr := kubernetes.ConvertLegionResourcesToK8s(mt.Spec.Resources)
		err = multierr.Append(err, resValidationErr)
	}

	return err
}

func (mtv *MtValidator) validateToolchain(mt *training.ModelTraining) (err error) {
	if len(mt.Spec.Toolchain) == 0 {
		err = multierr.Append(err, errors.New(ToolchainEmptyErrorMessage))

		return
	}

	toolchain, k8sErr := mtv.mtRepository.GetToolchainIntegration(mt.Spec.Toolchain)
	if k8sErr != nil {
		err = multierr.Append(err, k8sErr)

		return
	}

	if len(mt.Spec.Image) == 0 {
		logMT.Info("Toolchain image parameter is nil. Set the default value",
			"name", mt.ID, "image", toolchain.Spec.DefaultImage)
		mt.Spec.Image = toolchain.Spec.DefaultImage
	}

	return
}

func (mtv *MtValidator) validateVCS(mt *training.ModelTraining) (err error) {
	if len(mt.Spec.VCSName) == 0 {
		err = multierr.Append(err, errors.New(EmptyVcsNameMessageError))

		return
	}

	if vcs, k8sErr := mtv.connRepository.GetConnection(mt.Spec.VCSName); k8sErr != nil {
		logMT.Error(err, mtVcsNotExistsErrorMessage)

		err = multierr.Append(err, k8sErr)
	} else if len(mt.Spec.Reference) == 0 {
		switch {
		case vcs.Spec.Type != connection.GITType:
			err = multierr.Append(err, fmt.Errorf(WrongVcsTypeErrorMessage, vcs.Spec.Type))
		case len(vcs.Spec.Reference) == 0:
			err = multierr.Append(err, fmt.Errorf(WrongVcsReferenceErrorMessage, vcs.ID))
		default:
			logMT.Info("VCS reference parameter is nil. Set the default value",
				"name", mt.ID, "reference", vcs.Spec.Reference)
			mt.Spec.Reference = vcs.Spec.Reference
		}
	}

	return
}

func (mtv *MtValidator) validateMtData(mt *training.ModelTraining) (err error) {
	for i, dbd := range mt.Spec.Data {
		if len(dbd.LocalPath) == 0 {
			err = multierr.Append(err, fmt.Errorf(EmptyDataBindingPathErrorMessage, i))
		}

		if len(dbd.Connection) == 0 {
			err = multierr.Append(err, fmt.Errorf(EmptyDataBindingNameErrorMessage, i))

			continue
		}

		conn, k8sErr := mtv.connRepository.GetConnection(dbd.Connection)
		if k8sErr != nil {
			err = multierr.Append(err, k8sErr)

			continue
		}

		if _, ok := expectedConnectionDataTypes[conn.Spec.Type]; !ok {
			err = multierr.Append(err, fmt.Errorf(
				WrongDataBindingTypeErrorMessage,
				conn.ID, reflect.ValueOf(expectedConnectionDataTypes).MapKeys(),
			))
		}

	}

	return
}
