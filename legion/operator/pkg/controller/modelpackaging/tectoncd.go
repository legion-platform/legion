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

package modelpackaging

import (
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packaging_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	"github.com/spf13/viper"
	tektonv1alpha1 "github.com/tektoncd/pipeline/pkg/apis/pipeline/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"path"
)

const (
	configVolumeName            = "config"
	configDir                   = "/etc/legion"
	pathToPackagerBin           = "/opt/legion/packager"
	workspacePath               = "/workspace"
	resultPackagerContainerName = "result"
	packagerContainerName       = "packager"
	setupPackagerContainerName  = "setup"
	outputDir                   = "output"
)

func generatePackagerTaskSpec(
	packagingCR *legionv1alpha1.ModelPackaging,
	packagingIntegration *packaging.PackagingIntegration,
) (*tektonv1alpha1.TaskSpec, error) {
	mainPackagerStep, err := createMainPackagerStep(packagingCR, packagingIntegration)
	if err != nil {
		return nil, err
	}

	return &tektonv1alpha1.TaskSpec{
		Steps: []tektonv1alpha1.Step{
			createInitPackagerStep(), mainPackagerStep, createResultPackagerStep(),
		},
		Volumes: []corev1.Volume{
			{
				Name: configVolumeName,
				VolumeSource: corev1.VolumeSource{
					Secret: &corev1.SecretVolumeSource{
						SecretName: packagingCR.Name,
					},
				},
			},
		},
		StepTemplate: &corev1.Container{
			VolumeMounts: []corev1.VolumeMount{
				{
					Name:      configVolumeName,
					ReadOnly:  true,
					MountPath: configDir,
				},
			},
		},
	}, nil
}

func createInitPackagerStep() tektonv1alpha1.Step {
	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    setupPackagerContainerName,
			Image:   viper.GetString(packaging_conf.ModelPackagerImage),
			Command: []string{pathToPackagerBin},
			Args: []string{
				"--config",
				path.Join(configDir, packagerConfig),
				"setup",
				"--mp-file",
				path.Join(configDir, mpContentFile),
			},
			Resources: packagerResources,
		},
	}
}

func createMainPackagerStep(
	packagingCR *legionv1alpha1.ModelPackaging,
	packagingIntegration *packaging.PackagingIntegration) (tektonv1alpha1.Step, error) {
	packResources, err := kubernetes.ConvertLegionResourcesToK8s(packagingCR.Spec.Resources)
	if err != nil {
		log.Error(err, "The packaging resources is not valid",
			"mp id", packagingCR.Name, "resources", packagingCR.Namespace)

		return tektonv1alpha1.Step{}, err
	}

	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    packagerContainerName,
			Image:   packagingCR.Spec.Image,
			Command: []string{packagingIntegration.Spec.Entrypoint},
			Args: []string{
				path.Join(workspacePath, outputDir),
				path.Join(configDir, mpContentFile),
			},
			SecurityContext: &corev1.SecurityContext{
				Privileged:               &packagingPrivileged,
				AllowPrivilegeEscalation: &packagingPrivileged,
			},
			Resources: packResources,
		},
	}, nil
}

func createResultPackagerStep() tektonv1alpha1.Step {
	return tektonv1alpha1.Step{
		Container: corev1.Container{
			Name:    resultPackagerContainerName,
			Image:   viper.GetString(packaging_conf.ModelPackagerImage),
			Command: []string{pathToPackagerBin},
			Args: []string{
				"--config",
				path.Join(configDir, packagerConfig),
				"save",
				"--mp-file",
				path.Join(configDir, mpContentFile),
			},
			Resources: packagerResources,
		},
	}
}
