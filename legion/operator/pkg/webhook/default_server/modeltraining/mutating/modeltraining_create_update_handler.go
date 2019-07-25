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
	"net/http"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
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

func init() {
	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &ModelTrainingCreateUpdateHandler{})
}

type ModelTrainingCreateUpdateHandler struct {
	Client  client.Client
	Decoder types.Decoder
}

var _ admission.Handler = &ModelTrainingCreateUpdateHandler{}

func (h *ModelTrainingCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	mt := &legionv1alpha1.ModelTraining{}

	err := h.Decoder.Decode(req, mt)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	mtCopy := mt.DeepCopy()
	log.Info("Mutate the Model Training", "name", mt.Name)

	err = mtCopy.ValidatesAndSetDefaults(h.Client)
	if err != nil {
		log.Error(err, "Mutation process was failed for Model Training", "name", mtCopy.Name)
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}

	log.Info("Mutation process finished successfully for Model Training", "name", mt.Name, "before", mt, "after", mtCopy)

	return admission.PatchResponse(mt, mtCopy)
}

var _ inject.Client = &ModelTrainingCreateUpdateHandler{}

func (h *ModelTrainingCreateUpdateHandler) InjectClient(c client.Client) error {
	h.Client = c
	return nil
}

var _ inject.Decoder = &ModelTrainingCreateUpdateHandler{}

func (h *ModelTrainingCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
