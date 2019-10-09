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
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/training"
	config_deployment "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	mt_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/training"
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
	logMT       = logf.Log.WithName("model-training--repository")
	MDMaxSize   = 500
	MDFirstPage = 0
)

func mtTransformToLabels(mt *training.ModelTraining) map[string]string {
	return map[string]string{
		"toolchain":     mt.Spec.Toolchain,
		"model_name":    mt.Spec.Model.Name,
		"model_version": mt.Spec.Model.Version,
	}
}

func mtTransform(k8sMT *v1alpha1.ModelTraining) *training.ModelTraining {
	return &training.ModelTraining{
		ID:     k8sMT.Name,
		Spec:   k8sMT.Spec,
		Status: &k8sMT.Status,
	}
}

func (kc *trainingK8sRepository) SaveModelTrainingInfo(id string, info map[string]string) error {
	mt, err := kc.GetModelTraining(id)
	if err != nil {
		return err
	}

	trainingPod := &corev1.Pod{}
	trainingNamespacedName := types.NamespacedName{
		Name:      mt.ID,
		Namespace: kc.namespace,
	}
	if err := kc.k8sClient.Get(context.TODO(), trainingNamespacedName, trainingPod); err != nil {
		return err
	}

	if len(trainingPod.Annotations) == 0 {
		trainingPod.Annotations = map[string]string{}
	}

	for k, v := range info {
		trainingPod.Annotations[k] = v
	}

	return kc.k8sClient.Update(context.TODO(), trainingPod)
}

func (kc *trainingK8sRepository) GetModelTraining(id string) (*training.ModelTraining, error) {
	k8sMD := &v1alpha1.ModelTraining{}
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: kc.namespace},
		k8sMD,
	); err != nil {
		logMT.Error(err, "Get Model Training from k8s", "id", id)

		return nil, err
	}

	return mtTransform(k8sMD), nil
}

func (kc *trainingK8sRepository) GetModelTrainingList(options ...kubernetes.ListOption) (
	[]training.ModelTraining, error,
) {
	var k8sMDList v1alpha1.ModelTrainingList

	listOptions := &kubernetes.ListOptions{
		Filter: nil,
		Page:   &MDFirstPage,
		Size:   &MDMaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	labelSelector, err := kubernetes.TransformFilter(listOptions.Filter, mt_repository.TagKey)
	if err != nil {
		logMT.Error(err, "Generate label selector")
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
		}, &k8sMDList); err != nil {
			logMT.Error(err, "Get Model Training from k8s")

			return nil, err
		}

		continueToken = k8sMDList.ListMeta.Continue
		if *listOptions.Page != i && len(continueToken) == 0 {
			return nil, nil
		}
	}

	mts := make([]training.ModelTraining, len(k8sMDList.Items))
	for i := 0; i < len(k8sMDList.Items); i++ {
		currentMT := k8sMDList.Items[i]

		mts[i] = training.ModelTraining{ID: currentMT.Name, Spec: currentMT.Spec, Status: &currentMT.Status}
	}

	return mts, nil
}

func (kc *trainingK8sRepository) DeleteModelTraining(id string) error {
	mt := &v1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      id,
			Namespace: kc.namespace,
		},
	}

	if err := kc.k8sClient.Delete(context.TODO(), mt); err != nil {
		logMT.Error(err, "Delete Model Training from k8s", "id", id)

		return err
	}

	return nil
}

func (kc *trainingK8sRepository) UpdateModelTraining(mt *training.ModelTraining) error {
	var k8sMD v1alpha1.ModelTraining
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: mt.ID, Namespace: kc.namespace},
		&k8sMD,
	); err != nil {
		logMT.Error(err, "Get Model Training from k8s", "name", mt.ID)

		return err
	}

	// TODO: think about update, not replacing as for now
	k8sMD.Spec = mt.Spec
	k8sMD.Status.State = v1alpha1.ModelTrainingUnknown
	k8sMD.Status.ExitCode = nil
	k8sMD.Status.Reason = nil
	k8sMD.Status.Message = nil
	k8sMD.ObjectMeta.Labels = mtTransformToLabels(mt)

	if err := kc.k8sClient.Update(context.TODO(), &k8sMD); err != nil {
		logMT.Error(err, "Update of the Model Training", "name", mt.ID)

		return err
	}

	return nil
}

func (kc *trainingK8sRepository) CreateModelTraining(mt *training.ModelTraining) error {
	k8sMd := &v1alpha1.ModelTraining{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mt.ID,
			Namespace: kc.namespace,
			Labels:    mtTransformToLabels(mt),
		},
		Spec: mt.Spec,
	}

	if err := kc.k8sClient.Create(context.TODO(), k8sMd); err != nil {
		logMT.Error(err, "ModelTraining creation error from k8s", "name", mt.ID)

		return err
	}

	return nil
}

func (kc *trainingK8sRepository) GetModelTrainingLogs(id string, writer mt_repository.Writer, follow bool) error {
	var mt v1alpha1.ModelTraining
	if err := kc.k8sClient.Get(context.TODO(),
		types.NamespacedName{Name: id, Namespace: kc.namespace},
		&mt,
	); err != nil {
		return err
	} else if mt.Status.State != v1alpha1.ModelTrainingFailed &&
		mt.Status.State != v1alpha1.ModelTrainingRunning &&
		mt.Status.State != v1alpha1.ModelTrainingSucceeded {
		return fmt.Errorf("model Training %s has not started yet", id)
	}

	reader, err := utils.StreamLogs(kc.namespace, kc.k8sConfig, id, "trainer", follow)
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
					logMT.Error(err, "Error during coping of log stream")
					return nil
				}
				return err
			}

			writer.Flush()
		}
	}
}
