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

package kubernetes

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/packaging"
	config_deployment "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/util/kubernetes"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"io"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logMP       = logf.Log.WithName("model-packaging-repository")
	MpMaxSize   = 500
	MpFirstPage = 0
	// List of packager steps in execution order
	packagerContainerNames = []string{
		utils.TektonContainerName(legion.PackagerSetupStep),
		utils.TektonContainerName(legion.PackagerPackageStep),
		utils.TektonContainerName(legion.PackagerResultStep),
	}
	resultConfigKey = "result"
)

// TODO: add doc about map[string]interface{} https://github.com/kubernetes-sigs/kubebuilder/releases/tag/v2.0.0
func TransformMpFromK8s(mp *v1alpha1.ModelPackaging) (*packaging.ModelPackaging, error) {
	var arguments map[string]interface{}
	if err := json.Unmarshal([]byte(mp.Spec.Arguments), &arguments); err != nil {
		return nil, err
	}

	return &packaging.ModelPackaging{
		ID: mp.Name,
		Spec: packaging.ModelPackagingSpec{
			ArtifactName:    *mp.Spec.ArtifactName,
			IntegrationName: mp.Spec.Type,
			Image:           mp.Spec.Image,
			Arguments:       arguments,
			Targets:         mp.Spec.Targets,
			Resources:       mp.Spec.Resources,
		},
		Status: &mp.Status,
	}, nil
}

// Take a look to the documentation of TransformPackagingIntegrationFromK8s
func TransformMpToK8s(mp *packaging.ModelPackaging, k8sNamespace string) (*v1alpha1.ModelPackaging, error) {
	var mpStatus v1alpha1.ModelPackagingStatus
	if mp.Status != nil {
		mpStatus = *mp.Status
	}

	argumentsBytes, err := json.Marshal(mp.Spec.Arguments)
	if err != nil {
		return nil, err
	}

	return &v1alpha1.ModelPackaging{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mp.ID,
			Namespace: k8sNamespace,
			Labels: map[string]string{
				"type": mp.Spec.IntegrationName,
			},
		},
		Spec: v1alpha1.ModelPackagingSpec{
			ArtifactName: &mp.Spec.ArtifactName,
			Type:         mp.Spec.IntegrationName,
			Image:        mp.Spec.Image,
			Arguments:    string(argumentsBytes),
			Targets:      mp.Spec.Targets,
			Resources:    mp.Spec.Resources,
		},
		Status: mpStatus,
	}, nil
}

func (pkr *packagingK8sRepository) GetModelPackaging(id string) (*packaging.ModelPackaging, error) {
	k8sMp := &v1alpha1.ModelPackaging{}
	if err := pkr.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: pkr.namespace},
		k8sMp,
	); err != nil {
		logMP.Error(err, "Get Model Packaging from k8s", "id", id)

		return nil, err
	}

	return TransformMpFromK8s(k8sMp)
}

func (pkr *packagingK8sRepository) GetModelPackagingList(options ...kubernetes.ListOption) (
	[]packaging.ModelPackaging, error,
) {
	var k8sMpList v1alpha1.ModelPackagingList

	listOptions := &kubernetes.ListOptions{
		Filter: nil,
		Page:   &MpFirstPage,
		Size:   &MpMaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	labelSelector, err := kubernetes.TransformFilter(listOptions.Filter, mp_repository.TagKey)
	if err != nil {
		logMP.Error(err, "Generate label selector")
		return nil, err
	}
	continueToken := ""

	for i := 0; i < *listOptions.Page+1; i++ {
		if err := pkr.k8sClient.List(context.TODO(), &client.ListOptions{
			LabelSelector: labelSelector,
			Namespace:     pkr.namespace,
			Raw: &metav1.ListOptions{
				Limit:    int64(*listOptions.Size),
				Continue: continueToken,
			},
		}, &k8sMpList); err != nil {
			logMP.Error(err, "Get Model Packaging from k8s")

			return nil, err
		}

		continueToken = k8sMpList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	mps := make([]packaging.ModelPackaging, len(k8sMpList.Items))
	for i := 0; i < len(k8sMpList.Items); i++ {
		k8sMp := k8sMpList.Items[i]

		mp, err := TransformMpFromK8s(&k8sMp)
		if err != nil {
			return nil, err
		}

		mps[i] = *mp
	}

	return mps, nil
}

func (pkr *packagingK8sRepository) DeleteModelPackaging(id string) error {
	mp := &v1alpha1.ModelPackaging{
		ObjectMeta: metav1.ObjectMeta{
			Name:      id,
			Namespace: pkr.namespace,
		},
	}

	if err := pkr.k8sClient.Delete(context.TODO(), mp); err != nil {
		logMP.Error(err, "Delete Model Packaging from k8s", "id", id)

		return err
	}

	return nil
}

func (pkr *packagingK8sRepository) UpdateModelPackaging(mp *packaging.ModelPackaging) error {
	var k8sMp v1alpha1.ModelPackaging
	if err := pkr.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mp.ID, Namespace: pkr.namespace},
		&k8sMp,
	); err != nil {
		logMP.Error(err, "Get Model Packaging from k8s", "id", mp.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	updatedK8sMpSpec, err := TransformMpToK8s(mp, pkr.namespace)
	if err != nil {
		return err
	}

	k8sMp.Spec = updatedK8sMpSpec.Spec
	k8sMp.Status.State = v1alpha1.ModelPackagingUnknown
	k8sMp.Status.ExitCode = nil
	k8sMp.Status.Reason = nil
	k8sMp.Status.Message = nil
	k8sMp.Status.Results = []v1alpha1.ModelPackagingResult{}
	k8sMp.ObjectMeta.Labels = updatedK8sMpSpec.Labels

	if err := pkr.k8sClient.Update(context.TODO(), &k8sMp); err != nil {
		logMP.Error(err, "Creation of the Model Packaging", "id", mp.ID)

		return err
	}

	return nil
}

func (pkr *packagingK8sRepository) CreateModelPackaging(mp *packaging.ModelPackaging) error {
	k8sMp, err := TransformMpToK8s(mp, pkr.namespace)
	if err != nil {
		return err
	}

	if err := pkr.k8sClient.Create(context.TODO(), k8sMp); err != nil {
		logMP.Error(err, "Model packaging creation error from k8s", "id", mp.ID)

		return err
	}

	return nil
}

func (pkr *packagingK8sRepository) GetModelPackagingLogs(id string, writer mp_repository.Writer, follow bool) error {
	var mp v1alpha1.ModelPackaging
	if err := pkr.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: pkr.namespace},
		&mp,
	); err != nil {
		return err
	} else if mp.Status.State != v1alpha1.ModelPackagingSucceeded &&
		mp.Status.State != v1alpha1.ModelPackagingRunning &&
		mp.Status.State != v1alpha1.ModelPackagingFailed {
		return fmt.Errorf("model packaing %s has not started yet", id)
	}

	logReaders := make([]io.Reader, 0, len(packagerContainerNames))

	// Collect logs from all containers in execution order
	for _, containerName := range packagerContainerNames {
		reader, err := utils.StreamLogs(
			pkr.namespace,
			pkr.k8sConfig,
			mp.Status.PodName,
			containerName,
			follow,
		)
		if err != nil {
			return err
		}
		defer reader.Close()

		logReaders = append(logReaders, reader)
	}
	logReader := io.MultiReader(logReaders...)

	clientGone := writer.CloseNotify()
	for {
		logFlushSize := viper.GetInt64(config_deployment.ModelLogsFlushSize)

		select {
		case <-clientGone:
			return nil
		default:
			_, err := io.CopyN(writer, logReader, logFlushSize)
			if err != nil {
				if err == io.EOF {
					logMP.Error(err, "Error during coping of log stream")
					return nil
				}
				return err
			}

			writer.Flush()
		}
	}
}

func (pkr *packagingK8sRepository) SaveModelPackagingResult(id string, result []v1alpha1.ModelPackagingResult) error {
	resultStorage := &corev1.ConfigMap{}
	resultNamespacedName := types.NamespacedName{
		Name:      legion.GeneratePackageResultCMName(id),
		Namespace: pkr.namespace,
	}
	if err := pkr.k8sClient.Get(context.TODO(), resultNamespacedName, resultStorage); err != nil {
		logMP.Error(err, "Result config map must be present", "mp_id", id)
		return err
	}

	resultJSON, err := json.Marshal(result)
	if err != nil {
		return err
	}

	resultStorage.BinaryData = map[string][]byte{
		resultConfigKey: resultJSON,
	}

	return pkr.k8sClient.Update(context.TODO(), resultStorage)
}

func (pkr *packagingK8sRepository) GetModelPackagingResult(id string) ([]v1alpha1.ModelPackagingResult, error) {
	resultStorage := &corev1.ConfigMap{}
	resultNamespacedName := types.NamespacedName{
		Name:      legion.GeneratePackageResultCMName(id),
		Namespace: pkr.namespace,
	}
	if err := pkr.k8sClient.Get(context.TODO(), resultNamespacedName, resultStorage); err != nil {
		logMP.Error(err, "Result config map must be present", "mp_id", id)
		return nil, err
	}

	packResult := make([]v1alpha1.ModelPackagingResult, 0)
	if err := json.Unmarshal(resultStorage.BinaryData[resultConfigKey], &packResult); err != nil {
		return nil, err
	}

	return packResult, nil
}
