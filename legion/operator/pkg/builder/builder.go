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

package builder

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils"
	"github.com/pkg/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"math/rand"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("builder")

const (
	beginningOfContainerId = "docker://"
)

type ModelBuilder struct {
	config    legion.BuilderConfig
	clientset *kubernetes.Clientset
	k8sConfig *rest.Config
}

func NewModelBuilder(config legion.BuilderConfig) (*ModelBuilder, error) {
	k8sConfig, err := rest.InClusterConfig()
	if err != nil {
		log.Error(err, "Can't create k8s config")
		return nil, err
	}

	clientset, err := kubernetes.NewForConfig(k8sConfig)

	if err != nil {
		log.Error(err, "Can't create k8s client")
		return nil, err
	}

	return &ModelBuilder{
		config:    config,
		clientset: clientset,
		k8sConfig: k8sConfig,
	}, nil
}

// ModelConfig build contains the following steps:
//   1) Download specified git repository to the shared directory between model and builder pods
//   2) Start model entrypoint script\playbook
//   3) Extract model information from model file and save in annotations of current pod
//   3) Launch legionctl command to build a model docker image
func (mb *ModelBuilder) Start() (err error) {
	err = utils.CloneUserRepo(mb.config.SharedDirPath, mb.config.RepositoryURL, mb.config.GitSSHKeyPath, mb.config.Reference)
	if err != nil {
		log.Error(err, "Error occurs during cloning project")
		return err
	}

	commands := []string{
		"/bin/bash", "-c", fmt.Sprintf("cd %s && %s", mb.config.SharedDirPath, mb.config.Model.Command),
	}
	err = mb.execInModelPod(commands)
	if err != nil {
		log.Error(err, "Error occurs during execution of model command")
		return err
	}

	model, err := legion.ExtractModel(mb.config.Model.FilePath)
	if err != nil {
		log.Error(err, "Can't extract model from manifest file")
		return err
	}

	err = mb.buildModel(model)
	if err != nil {
		log.Error(err, "Error occurs during building model")
		return err
	}

	return
}

func (mb *ModelBuilder) updateAnnotations(newAnnotations map[string]string) error {
	podApi := mb.clientset.CoreV1().Pods(mb.config.Namespace)
	pod, err := podApi.Get(mb.config.PodName, metav1.GetOptions{})
	if err != nil {
		log.Error(err, "Getting the current pod")
		return err
	}

	annotations := pod.GetObjectMeta().GetAnnotations()
	if annotations == nil {
		annotations = make(map[string]string, 1)
	}

	for k, v := range newAnnotations {
		annotations[k] = v
	}

	pod.ObjectMeta.Annotations = annotations
	_, err = podApi.Update(pod)

	return err
}

func (mb *ModelBuilder) execInModelPod(commands []string) (err error) {
	stdout, stderr, err := utils.ExecToPodThroughAPI(commands, "model", mb.config.PodName,
		mb.config.Namespace)

	log.Info(fmt.Sprintf("Try to execute the following command: '%+v' in a model pod", commands))

	log.Info(fmt.Sprintf("Stdout: %s", stdout))
	log.Info(fmt.Sprintf("Stderr: %s", stderr))

	if err != nil {
		log.Error(err, "Execute command in model pod")
		return err
	}

	return
}

func (mb *ModelBuilder) getModelContainerID() (result string, err error) {
	pod, err := mb.clientset.CoreV1().Pods(mb.config.Namespace).Get(mb.config.PodName, metav1.GetOptions{})

	if err != nil {
		log.Error(err, "Can't get pod %s", pod.Name)
		return "", err
	}

	for _, container := range pod.Status.ContainerStatuses {
		if container.Name == "model" {
			return container.ContainerID[len(beginningOfContainerId):], nil
		}
	}

	return "", errors.New("Can't find container with `model` name")
}

func (mb *ModelBuilder) buildModel(model legion.Model) (err error) {
	containerID, err := mb.getModelContainerID()

	if err != nil {
		return err
	}

	localImageTag := fmt.Sprintf("legion_ci_%s_%s_%d", model.ID, model.Version, rand.Int())
	externalImageTag := legion.BuildModelImageName(mb.config.DockerRegistry, mb.config.ResultImagePrefix,
		model.ID, model.Version)

	// It's a hack to return the model information
	err = mb.updateAnnotations(map[string]string{
		legion.ModelImageKey:   externalImageTag,
		legion.ModelIDKey:      model.ID,
		legion.ModelVersionKey: model.Version,
	})
	if err != nil {
		return err
	}

	legionctlCmd := fmt.Sprintf("legionctl --verbose build --container-id %s --docker-image-tag %s "+
		"--push-to-registry %s --model-file %s", containerID, localImageTag, externalImageTag, mb.config.Model.FilePath,
	)
	commands := []string{
		"/bin/bash", "-c", fmt.Sprintf("cd %s && %s", mb.config.SharedDirPath, legionctlCmd),
	}

	if err = mb.execInModelPod(commands); err != nil {
		log.Error(err, "Run legionctl command")
		return
	}

	return
}
