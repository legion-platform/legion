#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
"""
Robot test library - kubernetes dashboard
"""
import time

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
from kubernetes.client import V1DeleteOptions, V1Pod, V1ObjectMeta, V1PodSpec, V1Toleration, V1Container, \
    V1ResourceRequirements
from kubernetes.client.rest import ApiException
import urllib3
from legion.robot.utils import wait_until

FAT_POD_MEMORY = "4Gi"
FAT_POD_CPU = "4"
FAT_POD_IMAGE = 'alpine:3.9.3'
FAT_POD_NAME = "fat-pod-name"


class K8s:
    """
    Kubernetes dashboard client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self, namespace):
        """
        Init client
        :param namespace: default k8s namespace
        """
        self._context = None
        self._information = None
        self._legion_group = 'legion.legion-platform.org'
        self._model_training_version = 'v1alpha1'
        self._namespace = namespace
        self._model_training_plural = 'modeltrainings'
        self._model_training_info = self._legion_group, self._model_training_version, \
                                    self._namespace, self._model_training_plural
        self._model_deployment_info = self._legion_group, 'v1alpha1', \
                                      self._namespace, 'modeldeployments'
        self._default_vcs = 'legion'

    def build_client(self):
        """
        Configure and returns kubernetes client

        :return: :py:module:`kubernetes.client`
        """
        try:
            kubernetes.config.load_incluster_config()
        except kubernetes.config.config_exception.ConfigException:
            kubernetes.config.load_kube_config(context=self._context)

        # Disable SSL warning for self-signed certificates
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return kubernetes.client.ApiClient()

    def choose_cluster_context(self, context=None):
        """
        Choose K8S connection context

        :param context: name of context
        :type context: str
        :return: None
        """
        self._context = context

        self.build_client()

    def start_fat_pod(self, node_taint_key, node_taint_value):
        """
        Start fat pod
        """
        client = self.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        pod = V1Pod(
            api_version='v1',
            kind='Pod',
            metadata=V1ObjectMeta(
                name=FAT_POD_NAME,
                annotations={
                    "sidecar.istio.io/inject": "false"
                },
            ),
            spec=V1PodSpec(
                restart_policy='Never',
                priority=0,
                tolerations=[
                    V1Toleration(
                        key=node_taint_key,
                        operator="Equal",
                        value=node_taint_value,
                        effect="NoSchedule",
                    )
                ],
                containers=[
                    V1Container(
                        name=FAT_POD_NAME,
                        image=FAT_POD_IMAGE,
                        resources=V1ResourceRequirements(
                            limits={'cpu': FAT_POD_CPU, 'memory': FAT_POD_MEMORY},
                            requests={'cpu': FAT_POD_CPU, 'memory': FAT_POD_MEMORY}
                        ),
                        command=["echo"],
                        args=["I am a fat :("]
                    )
                ]
            )
        )

        core_api.create_namespaced_pod(self._namespace, pod)

    def delete_fat_pod(self):
        """
        Delete fat pod
        """
        client = self.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        try:
            core_api.delete_namespaced_pod(FAT_POD_NAME, self._namespace,
                                           V1DeleteOptions(propagation_policy='Foreground',
                                                           grace_period_seconds=0))
        except ApiException as e:
            if e.status != 404:
                raise e

    def wait_fat_pod_completion(self):
        """
        Wait completion of fat pod
        """
        client = self.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        pod_completed_lambda = lambda: core_api.read_namespaced_pod(
            FAT_POD_NAME, self._namespace
        ).status.phase == "Succeeded"
        if not wait_until(pod_completed_lambda, iteration_duration=10, iterations=120):
            raise Exception("Timeout")

    def get_model_training_logs(self, name):
        """
        Get model training logs
        :param name: name of a model training resource
        :return: status
        """
        core_api = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient())

        return core_api.read_namespaced_pod_log(f'{name}-training-pod', self._namespace, container='builder')

    def check_all_containers_terminated(self, name):
        """
        Check that all pod containers are terminated
        :param name: name of a model training resource
        :return: None
        """
        core_api = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient())

        pod = core_api.read_namespaced_pod(f'{name}-training-pod', self._namespace)
        for container in pod.status.container_statuses:
            if not container.state.terminated:
                raise Exception(f'Container {container.name} of {pod.metadata.name} pod is still alive')

    def get_model_training_status(self, name):
        """
        Get model training status
        :param name: name of a model training resource
        :return: status
        """
        crds = kubernetes.client.CustomObjectsApi()

        model_training = crds.get_namespaced_custom_object(*self._model_training_info, name.lower())
        print(f'Fetched model training: {model_training}')

        status = model_training.get('status')
        return status if status else {}

    def get_model_deployment_status(self, name):
        """
        Get model training status
        :param name: name of a model training resource
        :return: status
        """
        crds = kubernetes.client.CustomObjectsApi()

        md = crds.get_namespaced_custom_object(*self._model_deployment_info, name.lower())
        print(f'Fetched model training: {md}')

        status = md.get('status')
        return status if status else {}

    def get_number_of_md_replicas(self, name, expected_number_of_replicas):
        """
        Get number of model deploymet replicas
        :param name: resource name
        :param expected_number_of_replicas: expected state
        :return:
        """
        md_status = self.get_model_deployment_status(name)
        return self.get_deployment_replicas(md_status["deployment"], self._namespace) == expected_number_of_replicas

    def wait_model_deployment_replicas(self, name, expected_number_of_replicas):
        """
        Wait specific status of a model training resource
        :param name: resource name
        :param expected_number_of_replicas: expected state
        """
        if not wait_until(lambda: self.get_number_of_md_replicas(name, expected_number_of_replicas),
                          iteration_duration=10, iterations=24):  # 4 min
            raise Exception(f"Timeout")

    def deployment_is_running(self, deployment_name, namespace):
        """
        Check that specific named deployment is okay (no one pending or failed pod)

        :param deployment_name: name of replication controller
        :type deployment_name: str
        :param namespace: name of namespace to look in
        :type namespace: str
        :raises: Exception
        :return: None
        """
        client = self.build_client()
        apps_api = kubernetes.client.AppsV1Api(client)

        deployment = apps_api.read_namespaced_deployment(deployment_name, namespace)

        if deployment.status.replicas != deployment.status.ready_replicas:
            raise Exception("Deployment '%s' is not ready: %d/%d replicas are running"
                            % (deployment_name, deployment.status.ready_replicas, deployment.status.replicas))

    def get_model_deployment(self, deployment_name):
        """
        Get dict of deployment by model name and version

        :param deployment_name: k8s deployment name
        :type deployment_name: str
        :return: k8s deployment object
        """
        client = self.build_client()
        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)

        return extension_api.read_namespaced_deployment(deployment_name, self._namespace)

    def get_deployment_replicas(self, deployment_name, namespace='default'):
        """
        Get number of replicas for a specified deployment from Kubernetes API

        :param deployment_name: name of a deployment
        :type deployment_name: str
        :param namespace: name of a namespace to look in
        :type namespace: str
        :return: number of replicas for a specified deployment
        :rtype int
        """
        client = self.build_client()
        apps_api = kubernetes.client.AppsV1Api(client)
        scale_data = apps_api.read_namespaced_deployment(deployment_name, namespace)
        print("Scale data for {} in {} ns is {}".format(deployment_name, namespace, scale_data))
        if scale_data is not None:
            return 0 if not scale_data.status.available_replicas else scale_data.status.available_replicas
        else:
            return None

    def wait_nodes_scale_down(self, node_taint_key, node_taint_value, timeout=600, sleep=60):
        """
        Wait finish of last job build

        :raises: Exception
        :return: None
        """
        client = self.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        timeout = int(timeout)
        sleep = int(sleep)
        start = time.time()
        time.sleep(sleep)

        while True:
            nodes_num = 0

            for node in core_api.list_node().items:
                if not node.spec.taints:
                    continue

                for taint in node.spec.taints:
                    if taint.key == node_taint_key and taint.value == node_taint_value:
                        nodes_num += 1
                        break

            elapsed = time.time() - start

            if nodes_num == 0:
                print('Scaled node was successfully unscaled after {} seconds'
                      .format(elapsed))
                return
            elif elapsed > timeout > 0:
                raise Exception('Node was not unscaled after {} seconds wait'.format(timeout))
            else:
                print(f'Current node count {nodes_num}. Sleep {sleep} seconds and try again')
                time.sleep(sleep)
