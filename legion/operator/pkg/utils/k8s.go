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
	"io"
	"net/http"

	core_v1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logk8s = logf.Log.WithName("legion_k8s")

type Writer interface {
	http.Flusher
	http.CloseNotifier
	io.Writer
}

// Stream logs from the pod to the writer object
// k8sConfig     - kubernetes config
// namespace     - namespace where pod is located
// podName       - kubernetes pod name
// containerName - container name of the pod
// writer        - logs will be streamed into this writer
// follow        - specify if the logs should be streamed
// logFlushSize  - size of the flushed logs per chunk
func StreamLogs(
	k8sConfig *rest.Config, namespace string, podName string,
	containerName string, writer Writer, follow bool, logFlushSize int64,
) error {
	clientset, _ := kubernetes.NewForConfig(k8sConfig)
	request := clientset.CoreV1().Pods(namespace).
		GetLogs(podName, &core_v1.PodLogOptions{Follow: follow, Container: containerName})

	reader, err := request.Stream()
	if err != nil {
		logk8s.Error(err, "open log stream")
		return err
	}
	defer reader.Close()

	clientGone := writer.CloseNotify()
	for {
		select {
		case <-clientGone:
			return nil
		default:
			_, err := io.CopyN(writer, reader, logFlushSize)
			if err != nil {
				if err == io.EOF {
					return nil
				}

				return err
			}

			writer.Flush()
		}
	}
}
