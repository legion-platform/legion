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
import urllib3

import legion.k8s.utils
import legion.k8s.properties
import legion.utils


class K8s:
    """
    Kubernetes dashboard client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        """
        Init client
        """
        self._context = None
        self._information = None

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
        legion.k8s.utils.CONNECTION_CONTEXT = context

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

        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
        if namespace is None:
            replica_sets = extension_api.list_replica_set_for_all_namespaces()
        else:
            replica_sets = extension_api.list_namespaced_replica_set(namespace)

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

    def replication_controller_is_running(self, replication_controller_name, namespace=None):
        """
        Check that specific named replication controller is okay (no one pending or failed pod)

        :param replication_controller_name: name of replication controller
        :type replication_controller_name: str
        :param namespace: name of namespace to look in
        :type namespace: str
        :raises: Exception
        :return: None
        """
        client = self.build_client()

        core_api = kubernetes.client.CoreV1Api(client)
        if namespace is None:
            replication_controllers = core_api.list_replication_controller_for_all_namespaces()
        else:
            replication_controllers = core_api.list_namespaced_replication_controller(namespace)

        for item in replication_controllers.items:
            if item.metadata.labels.get('component', '') == replication_controller_name:
                if item.status.replicas == item.status.ready_replicas:
                    return True
                else:
                    raise Exception("Replication controller '%s' is not ready: %d/%d replicas are running"
                                    % (replication_controller_name, item.status.ready_replicas, item.status.replicas))

        raise Exception("Replication controller '%s' wasn't found" % replication_controller_name)

    def get_deployment_replicas(self, deployment_name, namespace='default'):
        """
        Gets number of replicas for a specified deployment from Kubernetes API

        :param deployment_name: name of a deployment
        :type deployment_name: str
        :param namespace: name of a namespace to look in
        :type namespace: str
        :return: number of replicas for a specified deployment
        :rtype int
        """
        client = self.build_client()
        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
        scale_data = extension_api.read_namespaced_deployment_scale(deployment_name, namespace)
        if scale_data is not None:
            return scale_data.status.replicas
        else:
            return 0

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
        if type(replicas) != int or replicas <= 0:
            raise ValueError('"replicas" argument should be a positive number, but got "%s"' % replicas)
        client = self.build_client()
        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
        scale_data = extension_api.read_namespaced_deployment_scale(deployment_name, namespace)
        scale_data.spec.replicas = replicas
        extension_api.replace_namespaced_deployment_scale(deployment_name, namespace, scale_data)

    def update_model_property_key(self, namespace, model_id, model_version, key, value):
        """
        Update models config map property by key value

        :param namespace: name of namespace
        :param model_id: model ID
        :param model_version: model version
        :param key: key of config map
        :param value: new value for key
        :return: None
        """
        storage_name = legion.utils.model_properties_storage_name(model_id, model_version)
        property = legion.k8s.properties.K8SConfigMapStorage(storage_name, namespace)

        property.load()
        property[key] = value
        property.save()

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
        :param timeout: waiting timeout in seconds. 0 for disable (infinite)
        :type timeout: str or int
        :param sleep: sleep between checks in seconds
        :type sleep: str or int
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
