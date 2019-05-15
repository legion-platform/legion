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

package mutating

import (
	"context"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/pkg/errors"
	"github.com/spf13/viper"
	"k8s.io/apimachinery/pkg/api/resource"
	"net/http"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	k8stypes "k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/runtime/inject"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission/types"
)

const (
	webhookName = "mutating-create-update-modeltraining"
)

var log = logf.Log.WithName(webhookName)

var (
	defaultModelResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	defaultModelFileName = "/var/legion/robot.model"
)

func init() {
	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &ModelTrainingCreateUpdateHandler{})
}

// ModelTrainingCreateUpdateHandler handles ModelTraining
type ModelTrainingCreateUpdateHandler struct {
	Client  client.Client
	Decoder types.Decoder
}

func (h *ModelTrainingCreateUpdateHandler) mutatingModelTrainingFn(ctx context.Context, obj *legionv1alpha1.ModelTraining) error {
	if obj.Spec.Resources == nil {
		log.Info("Training resource parameter is nil. Set the default value",
			"name", obj.Name, "resources", defaultModelResources)
		obj.Spec.Resources = &defaultModelResources
	}

	if len(obj.Spec.ModelFile) == 0 {
		log.Info("Model file parameter is nil. Set the default value",
			"name", obj.Name, "model_file", defaultModelFileName)
		obj.Spec.ModelFile = defaultModelFileName
	}

	if len(obj.Spec.Image) == 0 {
		modelImage, err := legion.GetToolchainImage(obj.Spec.ToolchainType)

		if err != nil {
			log.Error(err, "Cannot extract a toolchain image")
			return err
		}

		log.Info("Toolchain image parameter is nil. Set the default value",
			"name", obj.Name, "image", modelImage)
		obj.Spec.Image = modelImage
	}

	vcsInstanceName := k8stypes.NamespacedName{
		Name:      obj.Spec.VCSName,
		Namespace: viper.GetString(legion.Namespace),
	}
	vcsCR := &legionv1alpha1.VCSCredential{}
	if err := h.Client.Get(context.TODO(), vcsInstanceName, vcsCR); err != nil {
		log.Error(err, "Cannot fetch VCS Credential with name")

		return err
	}

	if len(obj.Spec.Reference) == 0 {
		if len(vcsCR.Spec.DefaultReference) == 0 {
			return errors.New(fmt.Sprintf(
				"You should specify a reference of Model Training explicitly. Because %s does not have default reference",
				vcsCR.Name),
			)
		}

		log.Info("VCS reference parameter is nil. Set the default value",
			"name", obj.Name, "reference", vcsCR.Spec.DefaultReference)
		obj.Spec.Reference = vcsCR.Spec.DefaultReference
	}

	return nil
}

var _ admission.Handler = &ModelTrainingCreateUpdateHandler{}

// Handle handles admission requests.
func (h *ModelTrainingCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	obj := &legionv1alpha1.ModelTraining{}

	err := h.Decoder.Decode(req, obj)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	copy := obj.DeepCopy()
	log.Info("Mutate the Model Training", "name", copy.Name)

	err = h.mutatingModelTrainingFn(ctx, copy)
	if err != nil {
		log.Error(err, "Mutation process was failed", "name", copy.Name)
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}
	return admission.PatchResponse(obj, copy)
}

var _ inject.Client = &ModelTrainingCreateUpdateHandler{}

// InjectClient injects the client into the ModelTrainingCreateUpdateHandler
func (h *ModelTrainingCreateUpdateHandler) InjectClient(c client.Client) error {
	h.Client = c
	return nil
}

var _ inject.Decoder = &ModelTrainingCreateUpdateHandler{}

// InjectDecoder injects the decoder into the ModelTrainingCreateUpdateHandler
func (h *ModelTrainingCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
