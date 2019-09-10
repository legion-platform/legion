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

package deployment

import (
	"errors"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	config_deployment "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/spf13/viper"
	"go.uber.org/multierr"
)

const (
	EmptyImageErrorMessage             = "the image parameter is empty"
	MinReplicasErrorMessage            = "minimum number of replicas parameter must not be less than 0"
	MaxReplicasErrorMessage            = "maximum number of replicas parameter must not be less than 1"
	MinMoreThanMinReplicasErrorMessage = "minimum number of replicas parameter must not be less than maximum number of replicas parameter"
	ReadinessProbeErrorMessage         = "readiness probe must be positive number"
	LivenessProbeErrorMessage          = "liveness probe parameter must be positive number"
)

var (
	MdDefaultMinimumReplicas = int32(0)
	MdDefaultMaximumReplicas = int32(1)
	defaultMemoryLimit       = "256Mi"
	defaultCpuLimit          = "256m"
	defaultMemoryRequests    = "128Mi"
	defaultCpuRequests       = "128m"
	MdDefaultResources       = &v1alpha1.ResourceRequirements{
		Limits: &v1alpha1.ResourceList{
			Cpu:    &defaultCpuLimit,
			Memory: &defaultMemoryLimit,
		},
		Requests: &v1alpha1.ResourceList{
			Cpu:    &defaultCpuRequests,
			Memory: &defaultMemoryRequests,
		},
	}
	MdDefaultLivenessProbeInitialDelay  = int32(2)
	MdDefaultReadinessProbeInitialDelay = int32(2)
)

func ValidatesMDAndSetDefaults(md *deployment.ModelDeployment) (err error) {
	if len(md.Spec.Image) == 0 {
		err = multierr.Append(err, errors.New(EmptyImageErrorMessage))
	}

	if md.Spec.RoleName == nil || len(*md.Spec.RoleName) == 0 {
		logMD.Info("Role name parameter is nil or empty. Set the default value",
			"Deployment name", md.Id, "role name", MdDefaultMinimumReplicas)
		defaultRoleName := viper.GetString(config_deployment.DefaultRoleName)
		md.Spec.RoleName = &defaultRoleName
	}

	if md.Spec.MinReplicas == nil {
		logMD.Info("Minimum number of replicas parameter is nil. Set the default value",
			"Deployment name", md.Id, "replicas", MdDefaultMinimumReplicas)
		md.Spec.MinReplicas = &MdDefaultMinimumReplicas
	} else {
		if *md.Spec.MinReplicas < 0 {
			err = multierr.Append(errors.New(MinReplicasErrorMessage), err)
		}
	}

	if md.Spec.MaxReplicas == nil {
		logMD.Info("Maximum number of replicas parameter is nil. Set the default value",
			"Deployment name", md.Id, "replicas", MdDefaultMinimumReplicas)
		md.Spec.MaxReplicas = &MdDefaultMaximumReplicas
	} else {
		if *md.Spec.MaxReplicas < 1 {
			err = multierr.Append(errors.New(MaxReplicasErrorMessage), err)
		}
	}

	if md.Spec.MaxReplicas != nil && md.Spec.MinReplicas != nil && *md.Spec.MinReplicas > *md.Spec.MaxReplicas {
		err = multierr.Append(errors.New(MinMoreThanMinReplicasErrorMessage), err)
	}

	if md.Spec.Resources == nil {
		logMD.Info("Deployment resources parameter is nil. Set the default value",
			"name", md.Id, "resources", MdDefaultResources)
		md.Spec.Resources = MdDefaultResources
	}

	if md.Spec.ReadinessProbeInitialDelay == nil {
		logMD.Info("Readiness probe parameter is nil. Set the default value",
			"name", md.Id, "readiness_probe", MdDefaultReadinessProbeInitialDelay)
		md.Spec.ReadinessProbeInitialDelay = &MdDefaultReadinessProbeInitialDelay
	} else {
		if *md.Spec.ReadinessProbeInitialDelay <= 0 {
			err = multierr.Append(errors.New(ReadinessProbeErrorMessage), err)
		}
	}

	if md.Spec.LivenessProbeInitialDelay == nil {
		logMD.Info("Liveness probe parameter is nil. Set the default value",
			"name", md.Id, "replicas", MdDefaultLivenessProbeInitialDelay)

		md.Spec.LivenessProbeInitialDelay = &MdDefaultLivenessProbeInitialDelay
	} else {
		if *md.Spec.LivenessProbeInitialDelay <= 0 {
			err = multierr.Append(errors.New(LivenessProbeErrorMessage), err)
		}
	}

	return
}
