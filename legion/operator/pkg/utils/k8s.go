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

package utils

import (
	"bytes"
	"fmt"
	core_v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/remotecommand"
	"os"
	"path/filepath"
)

func GetClientConfig() (*rest.Config, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		fmt.Printf("Unable to create config. Error: %+v\n", err)

		err1 := err

		kubeconfig := filepath.Join(os.Getenv("HOME"), ".kube", "config")

		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
		if err != nil {
			err = fmt.Errorf("InClusterConfig as well as BuildConfigFromFlags Failed. Error in InClusterConfig: %+v\nError in BuildConfigFromFlags: %+v", err1, err)
			return nil, err
		}
	}

	return config, nil
}

func GetClientsetFromConfig(config *rest.Config) (*kubernetes.Clientset, error) {
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		err = fmt.Errorf("failed creating clientset. Error: %+v", err)
		return nil, err
	}

	return clientset, nil
}

func ExecToPodThroughAPI(command []string, containerName, podName, namespace string, config *rest.Config) error {
	clientset, err := GetClientsetFromConfig(config)
	if err != nil {
		return err
	}

	req := clientset.Core().RESTClient().Post().
		Resource("pods").
		Name(podName).
		Namespace(namespace).
		SubResource("exec")
	scheme := runtime.NewScheme()
	if err := core_v1.AddToScheme(scheme); err != nil {
		return fmt.Errorf("error adding to scheme: %v", err)
	}

	parameterCodec := runtime.NewParameterCodec(scheme)
	req.VersionedParams(&core_v1.PodExecOptions{
		Command:   command,
		Container: containerName,
		Stdout:    true,
		Stderr:    true,
		TTY:       false,
		Stdin:     false,
	}, parameterCodec)

	fmt.Println("Request URL:", req.URL().String())

	exec, err := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
	if err != nil {
		return fmt.Errorf("error while creating Executor: %v", err)
	}

	var stdout, stderr bytes.Buffer
	err = exec.Stream(remotecommand.StreamOptions{
		Stdout: &stdout,
		Stderr: &stderr,
		Tty:    false,
	})

	log.Info(fmt.Sprintf("Try to execute the following command: '%+v' in the %s container of the %s pod",
		command, containerName, podName))

	log.Info(fmt.Sprintf("Command [stdout='%s',stderr='%s']", stdout.String(), stderr.String()))

	if err != nil {
		return fmt.Errorf("error in Stream: %v", err)
	}

	return nil
}
