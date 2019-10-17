/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package packager

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	packager_conf "github.com/legion-platform/legion/legion/operator/pkg/config/packager"
	"github.com/spf13/viper"
)

// The function extracts data from a repository and creates the packaging entity.
func (p *Packager) getPackaging() (*packaging.K8sPackager, error) {
	modelPackaging, err := p.packRepo.GetModelPackaging(p.modelPackagingID)
	if err != nil {
		return nil, err
	}
	packagingIntegration, err := p.packRepo.GetPackagingIntegration(modelPackaging.Spec.IntegrationName)
	if err != nil {
		return nil, err
	}

	targets := make([]packaging.PackagerTarget, 0, len(modelPackaging.Spec.Targets))
	for _, target := range modelPackaging.Spec.Targets {
		conn, err := p.connRepo.GetConnection(target.ConnectionName)
		if err != nil {
			return nil, err
		}

		targets = append(targets, packaging.PackagerTarget{
			Name:       target.Name,
			Connection: *conn,
		})
	}

	modelHolder, err := p.connRepo.GetConnection(viper.GetString(packager_conf.OutputConnectionName))
	if err != nil {
		return nil, err
	}

	return &packaging.K8sPackager{
		ModelHolder:          modelHolder,
		ModelPackaging:       modelPackaging,
		PackagingIntegration: packagingIntegration,
		TrainingZipName:      modelPackaging.Spec.ArtifactName,
		Targets:              targets,
	}, nil
}
