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
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	mp_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/packaging"
	corev1 "k8s.io/api/core/v1"

	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/spf13/viper"
	"io"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var (
	logMP       = logf.Log.WithName("model-packaging--repository")
	MpMaxSize   = 500
	MpFirstPage = 0
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

func (kc *packagingK8sRepository) SaveModelPackagingResult(id string, info map[string]string) error {
	mp, err := kc.GetModelPackaging(id)
	if err != nil {
		return err
	}

	packagingPod := &corev1.Pod{}
	packagingNamespacedName := types.NamespacedName{
		Name:      mp.ID,
		Namespace: kc.namespace,
	}
	if err := kc.k8sClient.Get(context.TODO(), packagingNamespacedName, packagingPod); err != nil {
		return err
	}

	if len(packagingPod.Annotations) == 0 {
		packagingPod.Annotations = map[string]string{}
	}

	for k, v := range info {
		packagingPod.Annotations[k] = v
	}

	return kc.k8sClient.Update(context.TODO(), packagingPod)
}

func (kc *packagingK8sRepository) GetModelPackaging(id string) (*packaging.ModelPackaging, error) {
	k8sMp := &v1alpha1.ModelPackaging{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: kc.namespace},
		k8sMp,
	); err != nil {
		logMP.Error(err, "Get Model Packaging from k8s", "id", id)

		return nil, err
	}

	return TransformMpFromK8s(k8sMp)
}

func (kc *packagingK8sRepository) GetModelPackagingList(options ...kubernetes.ListOption) (
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
		if err := kc.k8sClient.List(context.TODO(), &client.ListOptions{
			LabelSelector: labelSelector,
			Namespace:     kc.namespace,
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

func (kc *packagingK8sRepository) DeleteModelPackaging(id string) error {
	mp := &v1alpha1.ModelPackaging{
		ObjectMeta: metav1.ObjectMeta{
			Name:      id,
			Namespace: kc.namespace,
		},
	}

	if err := kc.k8sClient.Delete(context.TODO(), mp); err != nil {
		logMP.Error(err, "Delete Model Packaging from k8s", "id", id)

		return err
	}

	return nil
}

func (kc *packagingK8sRepository) UpdateModelPackaging(mp *packaging.ModelPackaging) error {
	var k8sMp v1alpha1.ModelPackaging
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mp.ID, Namespace: kc.namespace},
		&k8sMp,
	); err != nil {
		logMP.Error(err, "Get Model Packaging from k8s", "id", mp.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	updatedK8sMpSpec, err := TransformMpToK8s(mp, kc.namespace)
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

	if err := kc.k8sClient.Update(context.TODO(), &k8sMp); err != nil {
		logMP.Error(err, "Creation of the Model Packaging", "id", mp.ID)

		return err
	}

	return nil
}

func (kc *packagingK8sRepository) CreateModelPackaging(mp *packaging.ModelPackaging) error {
	k8sMp, err := TransformMpToK8s(mp, kc.namespace)
	if err != nil {
		return err
	}

	if err := kc.k8sClient.Create(context.TODO(), k8sMp); err != nil {
		logMP.Error(err, "Model packaging creation error from k8s", "id", mp.ID)

		return err
	}

	return nil
}

func (kc *packagingK8sRepository) GetModelPackagingLogs(id string, writer mp_repository.Writer, follow bool) error {
	var mp v1alpha1.ModelPackaging
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: kc.namespace},
		&mp,
	); err != nil {
		return err
	} else if mp.Status.State != v1alpha1.ModelPackagingSucceeded &&
		mp.Status.State != v1alpha1.ModelPackagingRunning &&
		mp.Status.State != v1alpha1.ModelPackagingFailed {
		return fmt.Errorf("model packaing %s has not started yet", id)
	}

	reader, err := utils.StreamLogs(kc.namespace, kc.k8sConfig, id, "packager", follow)
	if err != nil {
		return err
	}
	defer reader.Close()
	clientGone := writer.CloseNotify()
	for {
		logFlushSize := viper.GetInt64(config_deployment.ModelLogsFlushSize)

		select {
		case <-clientGone:
			return nil
		default:
			_, err := io.CopyN(writer, reader, logFlushSize)
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
