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
	"encoding/base64"
	"fmt"
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
	webhookName := "validating-create-update-vcscredential"
	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &VCSCredentialCreateUpdateHandler{})
}

// VCSCredentialCreateUpdateHandler handles VCSCredential
type VCSCredentialCreateUpdateHandler struct {
	Decoder types.Decoder
}

func (h *VCSCredentialCreateUpdateHandler) validatingVCSCredentialFn(ctx context.Context, obj *legionv1alpha1.VCSCredential) (bool, string, error) {
	// Check that credential is base64 encoded
	if len(obj.Spec.Credential) != 0 {
		_, err := base64.StdEncoding.DecodeString(obj.Spec.Credential)

		if err != nil {
			return false,
				fmt.Sprintf("Can't decode credential as base64 format: %s", obj.Spec.Credential), nil
		}
	}

	// Check that publicKey is base64 encoded
	if len(obj.Spec.PublicKey) != 0 {
		_, err := base64.StdEncoding.DecodeString(obj.Spec.PublicKey)

		if err != nil {
			return false,
				fmt.Sprintf("Can't decode PublicKey as base64 format: %s", obj.Spec.Credential), nil
		}
	}

	return true, "allowed to be admitted", nil
}

var _ admission.Handler = &VCSCredentialCreateUpdateHandler{}

// Handle handles admission requests.
func (h *VCSCredentialCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	obj := &legionv1alpha1.VCSCredential{}

	err := h.Decoder.Decode(req, obj)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	log.Info("Validating of the VCS Credential", "name", obj.Name)

	allowed, reason, err := h.validatingVCSCredentialFn(ctx, obj)
	if err != nil {
		log.Error(err, "Validation process was failed", "name", obj.Name)
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}
	return admission.ValidationResponse(allowed, reason)
}

var _ inject.Decoder = &VCSCredentialCreateUpdateHandler{}

// InjectDecoder injects the decoder into the VCSCredentialCreateUpdateHandler
func (h *VCSCredentialCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
