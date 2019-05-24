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

package validating

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
	webhookName = "validating-create-update-vcscredential"
)

var log = logf.Log.WithName(webhookName)

func init() {
	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &VCSCredentialCreateUpdateHandler{})
}

// VCSCredentialCreateUpdateHandler handles VCSCredential
type VCSCredentialCreateUpdateHandler struct {
	Decoder types.Decoder
}

func (h *VCSCredentialCreateUpdateHandler) validatingVCSCredentialFn(ctx context.Context, vcs *legionv1alpha1.VCSCredential) (bool, string, error) {
	if err := vcs.ValidatesAndSetDefaults(); err != nil {
		log.Info("VCS Credential validation error", "error", err.Error(), "name", vcs.Name)

		return false, err.Error(), nil
	}

	return true, "allowed to be admitted", nil
}

var _ admission.Handler = &VCSCredentialCreateUpdateHandler{}

// Handle handles admission requests.
func (h *VCSCredentialCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	vcs := &legionv1alpha1.VCSCredential{}

	err := h.Decoder.Decode(req, vcs)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	log.Info("Validating of the VCS Credential", "name", vcs.Name)

	allowed, reason, err := h.validatingVCSCredentialFn(ctx, vcs)
	if err != nil {
		log.Error(err, "Validation process was failed", "name", vcs.Name, "error", err.Error())
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}

	log.Info("Validation finished successfully for VCS Credential", "name", vcs.Name)

	return admission.ValidationResponse(allowed, reason)
}

var _ inject.Decoder = &VCSCredentialCreateUpdateHandler{}

// InjectDecoder injects the decoder into the VCSCredentialCreateUpdateHandler
func (h *VCSCredentialCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
