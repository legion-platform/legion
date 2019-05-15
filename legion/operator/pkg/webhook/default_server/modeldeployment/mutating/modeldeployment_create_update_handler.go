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
	"github.com/pkg/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	"net/http"

	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/controller-runtime/pkg/runtime/inject"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission/types"
)

const (
	webhookName = "mutating-create-update-modeldeployment"
)

var log = logf.Log.WithName(webhookName)

var (
	defaultNumberOfReplicas         = int32(1)
	defaultModelDeploymentResources = &corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	defaultLivenessProbeInitialDelay  = int32(2)
	defaultReadinessProbeInitialDelay = int32(2)
)

func init() {

	if HandlerMap[webhookName] == nil {
		HandlerMap[webhookName] = []admission.Handler{}
	}
	HandlerMap[webhookName] = append(HandlerMap[webhookName], &ModelDeploymentCreateUpdateHandler{})
}

// ModelDeploymentCreateUpdateHandler handles ModelDeployment
type ModelDeploymentCreateUpdateHandler struct {
	Decoder types.Decoder
}

func (h *ModelDeploymentCreateUpdateHandler) mutatingModelDeploymentFn(ctx context.Context, obj *legionv1alpha1.ModelDeployment) error {
	if obj.Spec.Replicas == nil {
		log.Info("Number of replicas parameter is nil. Set the default value",
			"name", obj.Name, "replicas", defaultNumberOfReplicas)
		obj.Spec.Replicas = &defaultNumberOfReplicas
	} else {
		if *obj.Spec.Replicas < 0 {
			return errors.New("Number of replicas parameter must not be less than 0")
		}
	}

	if obj.Spec.Resources == nil {
		log.Info("Deployment resources parameter is nil. Set the default value",
			"name", obj.Name, "resources", defaultNumberOfReplicas)
		obj.Spec.Resources = defaultModelDeploymentResources
	}

	if obj.Spec.ReadinessProbeInitialDelay == nil {
		log.Info("Readiness probe parameter is nil. Set the default value",
			"name", obj.Name, "readiness_probe", defaultReadinessProbeInitialDelay)
		obj.Spec.ReadinessProbeInitialDelay = &defaultReadinessProbeInitialDelay
	} else {
		if *obj.Spec.ReadinessProbeInitialDelay <= 0 {
			return errors.New(fmt.Sprintf("Readiness probe must be positive number. Current value is %d",
				*obj.Spec.ReadinessProbeInitialDelay))
		}
	}

	if obj.Spec.LivenessProbeInitialDelay == nil {
		log.Info("Liveness probe parameter is nil. Set the default value",
			"name", obj.Name, "replicas", defaultLivenessProbeInitialDelay)

		obj.Spec.LivenessProbeInitialDelay = &defaultLivenessProbeInitialDelay
	} else {
		if *obj.Spec.LivenessProbeInitialDelay <= 0 {
			return errors.New(fmt.Sprintf("Liveness probe parameter must be positive number. Current value is %d",
				*obj.Spec.LivenessProbeInitialDelay))
		}
	}

	return nil
}

var _ admission.Handler = &ModelDeploymentCreateUpdateHandler{}

// Handle handles admission requests.
func (h *ModelDeploymentCreateUpdateHandler) Handle(ctx context.Context, req types.Request) types.Response {
	obj := &legionv1alpha1.ModelDeployment{}

	err := h.Decoder.Decode(req, obj)
	if err != nil {
		return admission.ErrorResponse(http.StatusBadRequest, err)
	}
	copy := obj.DeepCopy()
	log.Info("Mutate the Model Deployment", "name", copy.Name)

	err = h.mutatingModelDeploymentFn(ctx, copy)
	if err != nil {
		log.Error(err, "Mutation process was failed", "name", copy.Name)
		return admission.ErrorResponse(http.StatusInternalServerError, err)
	}
	return admission.PatchResponse(obj, copy)
}

var _ inject.Decoder = &ModelDeploymentCreateUpdateHandler{}

// InjectDecoder injects the decoder into the ModelDeploymentCreateUpdateHandler
func (h *ModelDeploymentCreateUpdateHandler) InjectDecoder(d types.Decoder) error {
	h.Decoder = d
	return nil
}
