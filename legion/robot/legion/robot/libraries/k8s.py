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
from kubernetes.client import V1DeleteOptions, V1Pod, V1ObjectMeta, V1PodSpec, V1Toleration, V1Container, \
    V1ResourceRequirements
from kubernetes.client.rest import ApiException
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import yaml
from legion.robot.utils import wait_until
from legion.services.k8s import utils as k8s_utils

FAT_POD_MEMORY = "4Gi"
FAT_POD_CPU = "7"
FAT_POD_IMAGE = 'alpine:3.9.3'
FAT_POD_NAME = "fat-pod-name"


def generate_stub_model(model_id: str, model_version: str) -> str:
    """
    Generate name for stub model training custom resource
    :param model_id: model id
    :param model_version: model version
    :return: name
    """
    return f"stub-model-{model_id}-{model_version}"


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
        self._model_training_group = 'legion.legion-platform.org'
        self._model_training_version = 'v1alpha1'
        self._namespace = namespace
        self._model_training_plural = 'modeltrainings'
        self._model_training_info = self._model_training_group, self._model_training_version, \
                                    self._namespace, self._model_training_plural
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
        k8s_utils.CONNECTION_CONTEXT = context

        self.build_client()

    def start_fat_pod(self):
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
            ),
            spec=V1PodSpec(
                restart_policy='Never',
                priority=0,
                tolerations=[
                    V1Toleration(
                        key="dedicated",
                        operator="Equal",
                        value="jenkins-slave",
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
        if not wait_until(pod_completed_lambda, iteration_duration=10, iterations=78):
            raise Exception("Timeout")

    def delete_stub_model_training(self, model_id, model_version):
        """
        Delete model training resource
        :param model_id: model id
        :param model_version: model version
        """
        self.delete_model_training(generate_stub_model(model_id, model_version))

    def delete_model_training(self, name):
        """
        Delete model trainig resource
        :param name: name of training resource
        """
        crds = kubernetes.client.CustomObjectsApi()

        try:
            crds.delete_namespaced_custom_object(*self._model_training_info, name.lower(),
                                                 V1DeleteOptions(propagation_policy='Foreground',
                                                                 grace_period_seconds=0))
        except ApiException as e:
            if e.status != 404:
                raise e

    def create_stub_model_training(self, model_id, model_version):
        """
        Create model training resource
        :param model_id: model id
        :param model_version: modle version
        """
        crds = kubernetes.client.CustomObjectsApi()

        crds.create_namespaced_custom_object(
            *self._model_training_info,
            {
                "apiVersion": "legion.legion-platform.org/v1alpha1",
                "kind": "ModelTraining",
                "metadata": {
                    "name": generate_stub_model(model_id, model_version)
                },
                "spec": {
                    "entrypoint": 'legion/tests/e2e/models/simple.py',
                    'args': ['--id', model_id, '--version', model_version],
                    "toolchain": "python",
                    "vcsName": self._default_vcs
                }
            }
        )

    def create_model_training_from_yaml(self, path_to_file):
        """
        Create model training resource by yaml template
        :param path_to_file: path to yaml template
        """
        crds = kubernetes.client.CustomObjectsApi()

        with open(path_to_file) as f:
            model_training = yaml.safe_load(f)
            crds.create_namespaced_custom_object(
                *self._model_training_info,
                model_training
            )

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

    def build_stub_model(self, model_id, model_version):
        """
        Full lifecycle of model training resource
        :param model_id: model id
        :param model_version: model version
        :return: status of a model training resource
        """
        self.delete_stub_model_training(model_id, model_version)
        self.create_stub_model_training(model_id, model_version)
        self.wait_stub_model_training(model_id, model_version)

        return self.get_stub_model_training_status(model_id, model_version)

    def get_stub_model_training_status(self, model_id, model_version):
        """
        Get stub model training resource status
        :param model_id: model id
        :param model_version: model version
        :return:
        """
        return self.get_model_training_status(generate_stub_model(model_id, model_version))

    def wait_stub_model_training(self, model_id, model_version, expected_state="succeeded"):
        """
        Wait specific status of a stub model training resource
        :param model_id: model id
        :param model_version: model version
        :param expected_state: expected state
        :return:
        """
        return self.wait_model_training(generate_stub_model(model_id, model_version), expected_state)

    def wait_model_training(self, name, expected_state="succeeded"):
        """
        Wait specific status of a model training resource
        :param name: resource name
        :param expected_state: expected state
        """
        if not wait_until(lambda: self.get_model_training_status(name.lower()).get("state") == expected_state,
                          iteration_duration=10, iterations=36):
            raise Exception(f"Timeout")

    def service_is_running(self, service_name, namespace=None):
        """
        Check that specific named service is okay (no one pending or failed pod)

        :param service_name: name of replica set
        :type service_name: str
        :param namespace: name of namespace to look in
        :type namespace: str
        :raises: Exception
        :return: None
        """
        client = self.build_client()

        core_api = kubernetes.client.CoreV1Api(client)
        if namespace is None:
            services = core_api.list_service_for_all_namespaces()
        else:
            services = core_api.list_namespaced_service(namespace)

        for item in services.items:
            if item.metadata.name == service_name:
                return True
        raise Exception("Service '%s' wasn't found" % service_name)

    def replica_set_is_running(self, replica_set_name, namespace=None):
        """
        Check that specific named replica set is okay (no one pending or failed pod)

        :param replica_set_name: name of replica set
        :type replica_set_name: str
        :param namespace: name of namespace to look in
        :type namespace: str
        :raises: Exception
        :return: None
        """
        client = self.build_client()

        apps_api = kubernetes.client.AppsV1Api(client)
        if namespace is None:
            replica_sets = apps_api.list_replica_set_for_all_namespaces()
        else:
            replica_sets = apps_api.list_namespaced_replica_set(namespace)

        for item in replica_sets.items:
            if item.metadata.labels.get('app', '') == replica_set_name:
                if item.status.replicas == item.status.ready_replicas:
                    return True
                else:
                    raise Exception("Replica set '%s' is not ready: %d/%d replicas are running"
                                    % (replica_set_name, item.status.ready_replicas, item.status.replicas))

        raise Exception("Replica set '%s' wasn't found" % replica_set_name)

    def stateful_set_is_running(self, stateful_set_name, namespace=None):
        """
        Check that specific named stateful set is okay (no one pending or failed pod)

        :param stateful_set_name: name of stateful set
        :type stateful_set_name: str
        :param namespace: name of namespace to look in
        :type namespace: str
        :raises: Exception
        :return: None
        """
        client = self.build_client()

        app_api = kubernetes.client.AppsV1Api(client)
        if namespace is None:
            replica_sets = app_api.list_stateful_set_for_all_namespaces()
        else:
            replica_sets = app_api.list_namespaced_stateful_set(namespace)

        for item in replica_sets.items:
            if item.metadata.labels.get('app', '') == stateful_set_name:
                return True

        raise Exception("Stateful set '%s' wasn't found" % stateful_set_name)

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

    def get_model_deployment(self, model_id, model_version, namespace):
        """
        Get dict of deployment by model id and version

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param namespace: name of a namespace to look in
        :type namespace: str
        :return: number of replicas for a specified deployment
        :rtype int
        """
        client = self.build_client()
        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
        label_selector = 'component=legion-model,com.epam.legion.model.id={},com.epam.legion.model.version={}'.format(
            model_id, model_version
        )
        deployments = extension_api.list_namespaced_deployment(namespace, label_selector=label_selector)

        return deployments.items[0] if deployments else None

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
        scale_data = apps_api.read_namespaced_deployment_scale(deployment_name, namespace)
        print("Scale data for {} in {} enclave is {}".format(deployment_name, namespace, scale_data))
        if scale_data is not None:
            return scale_data.status.replicas
        else:
            return 0

    def wait_deployment_replicas_count(self, deployment_name, namespace='default', expected_replicas_num=1):
        """
        Wait for expected number of replicas for a specified deployment from Kubernetes API

        :param deployment_name: name of a deployment
        :type deployment_name: str
        :param namespace: name of a namespace to look in
        :type namespace: str
        :param expected_replicas_num: expected replicas number
        :type expected_replicas_num: str
        :return: None
        """
        expected_replicas_num = int(expected_replicas_num)
        result = wait_until(lambda: self.get_deployment_replicas(deployment_name, namespace) == expected_replicas_num,
                            iteration_duration=5, iterations=35)
        if not result:
            raise Exception("Expected ready replicas count '{}' does not match actual '{}'"
                            .format(expected_replicas_num, self.get_deployment_replicas(deployment_name, namespace)))

    def set_deployment_replicas(self, replicas, deployment_name, namespace='default'):
        """
        Update number of replicas for a specified deployment from Kubernetes API

        :param replicas: a new number of replicas
        :type replicas: int
        :param deployment_name: name of a deployment
        :type deployment_name: str
        :param namespace: name of a namespace to look in
        :type namespace: str
        :return: None
        """
        if not isinstance(replicas, int) or replicas <= 0:
            raise ValueError('"replicas" argument should be a positive number, but got "%s"' % replicas)
        client = self.build_client()
        apps_api = kubernetes.client.AppsV1Api(client)
        scale_data = apps_api.read_namespaced_deployment_scale(deployment_name, namespace)
        print("Scale data for {} in {} enclave is {}".format(deployment_name, namespace, scale_data))
        scale_data.spec.replicas = replicas
        print("Setting replica to {} for {} in {} enclave".format(replicas, deployment_name, namespace))
        apps_api.replace_namespaced_deployment_scale(deployment_name, namespace, scale_data)
        print("Replica to {} for {} in {} enclave was set up".format(replicas, deployment_name, namespace))

    def get_cluster_nodes(self):
        """
        Get current nodes by Kubernetes API

        :return: V1NodeList
        """
        client = self.build_client()
        core_api = kubernetes.client.CoreV1Api(client)
        nodes = core_api.list_node().items
        return nodes

    def wait_node_scale_down(self, expected_count, timeout=600, sleep=10):
        """
        Wait finish of last job build

        :param expected_count: expected node count
        :type expected_count: int
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
            nodes_num = len(core_api.list_node().items)
            elapsed = time.time() - start
            if nodes_num == expected_count:
                print('Scaled node was successfully unscaled after {} seconds'
                      .format(elapsed))
                return
            elif elapsed > timeout > 0:
                raise Exception('Node was not unscaled after {} seconds wait'.format(timeout))
            else:
                print('Current node count {}, but not as expected {}. Sleep {} seconds and try again'
                      .format(nodes_num, expected_count, sleep))
                time.sleep(sleep)
