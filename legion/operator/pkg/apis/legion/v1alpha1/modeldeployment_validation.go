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

package v1alpha1

import (
	"errors"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	"go.uber.org/multierr"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	mdEmptyImageErrorMessage             = "the image parameter is empty"
	mdMinReplicasErrorMessage            = "minimum number of replicas parameter must not be less than 0"
	mdMaxReplicasErrorMessage            = "maximum number of replicas parameter must not be less than 1"
	mdMinMoreThanMinReplicasErrorMessage = "minimum number of replicas parameter must not be less than maximum number of replicas parameter"
	mdReadinessProbeErrorMessage         = "readiness probe must be positive number"
	mdLivenessProbeErrorMessage          = "liveness probe parameter must be positive number"
)

var logMD = logf.Log.WithName("model_deployment")

var (
	mdDefaultMinimumReplicas = int32(0)
	mdDefaultMaximumReplicas = int32(1)
	mdDefaultResources       = &corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	mdDefaultLivenessProbeInitialDelay  = int32(2)
	mdDefaultReadinessProbeInitialDelay = int32(2)
)

func (md *ModelDeployment) ValidatesAndSetDefaults() (err error) {
	if len(md.Spec.Image) == 0 {
		err = multierr.Append(err, errors.New(mdEmptyImageErrorMessage))
	}

	if md.Spec.RoleName == nil || len(*md.Spec.RoleName) == 0 {
		logMD.Info("Role name parameter is nil or empty. Set the default value",
			"Deployment name", md.Name, "role name", mdDefaultMinimumReplicas)
		defaultRoleName := viper.GetString(legion.DefaultRoleName)
		md.Spec.RoleName = &defaultRoleName
	}

	if md.Spec.MinReplicas == nil {
		logMD.Info("Minimum number of replicas parameter is nil. Set the default value",
			"Deployment name", md.Name, "replicas", mdDefaultMinimumReplicas)
		md.Spec.MinReplicas = &mdDefaultMinimumReplicas
	} else {
		if *md.Spec.MinReplicas < 0 {
			err = multierr.Append(errors.New(mdMinReplicasErrorMessage), err)
		}
	}

	if md.Spec.MaxReplicas == nil {
		logMD.Info("Maximum number of replicas parameter is nil. Set the default value",
			"Deployment name", md.Name, "replicas", mdDefaultMinimumReplicas)
		md.Spec.MaxReplicas = &mdDefaultMaximumReplicas
	} else {
		if *md.Spec.MaxReplicas < 1 {
			err = multierr.Append(errors.New(mdMaxReplicasErrorMessage), err)
		}
	}

	if md.Spec.MaxReplicas != nil && md.Spec.MinReplicas != nil && *md.Spec.MinReplicas > *md.Spec.MaxReplicas {
		err = multierr.Append(errors.New(mdMinMoreThanMinReplicasErrorMessage), err)
	}

	if md.Spec.Resources == nil {
		logMD.Info("Deployment resources parameter is nil. Set the default value",
			"name", md.Name, "resources", mdDefaultResources)
		md.Spec.Resources = mdDefaultResources
	}

	if md.Spec.ReadinessProbeInitialDelay == nil {
		logMD.Info("Readiness probe parameter is nil. Set the default value",
			"name", md.Name, "readiness_probe", mdDefaultReadinessProbeInitialDelay)
		md.Spec.ReadinessProbeInitialDelay = &mdDefaultReadinessProbeInitialDelay
	} else {
		if *md.Spec.ReadinessProbeInitialDelay <= 0 {
			err = multierr.Append(errors.New(mdReadinessProbeErrorMessage), err)
		}
	}

	if md.Spec.LivenessProbeInitialDelay == nil {
		logMD.Info("Liveness probe parameter is nil. Set the default value",
			"name", md.Name, "replicas", mdDefaultLivenessProbeInitialDelay)

		md.Spec.LivenessProbeInitialDelay = &mdDefaultLivenessProbeInitialDelay
	} else {
		if *md.Spec.LivenessProbeInitialDelay <= 0 {
			err = multierr.Append(errors.New(mdLivenessProbeErrorMessage), err)
		}
	}

	return
}
