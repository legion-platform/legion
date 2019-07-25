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
	"sigs.k8s.io/controller-runtime/pkg/runtime/inject"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission/types"
)

const (
	webhookName = "mutating-create-update-modeldeployment"
)

var log = logf.Log.WithName(webhookName)

func init() {
	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &ModelDeploymentCreateUpdateHandler{})
}

type ModelDeploymentCreateUpdateHandler struct {
	Decoder types.Decoder
}

var _ admission.Handler = &ModelDeploymentCreateUpdateHandler{}

func (h *ModelDeploymentCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	md := &legionv1alpha1.ModelDeployment{}

	err := h.Decoder.Decode(req, md)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	mdCopy := md.DeepCopy()
	log.Info("Mutate the Model Deployment", "name", mdCopy.Name)

	err = mdCopy.ValidatesAndSetDefaults()
	if err != nil {
		log.Info("Mutation process was failed for Model Deployment", "name", md.Name, "error", err.Error(), "name", mdCopy.Name)
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}

	log.Info("Mutation process finished successfully for Model Deployment", "name", md.Name, "before", md, "after", mdCopy)

	return admission.PatchResponse(md, mdCopy)
}

var _ inject.Decoder = &ModelDeploymentCreateUpdateHandler{}

func (h *ModelDeploymentCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
