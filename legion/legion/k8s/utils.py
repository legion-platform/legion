#
#    Copyright 2018 EPAM Systems
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
legion k8s utils functions
"""
import os
import os.path
import logging

import docker
import docker.errors
import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import urllib3.exceptions
import yaml

import legion
import legion.containers.docker
import legion.containers.headers
import legion.config
import legion.external.grafana
from legion.utils import normalize_name
import legion.k8s.services
import legion.k8s.enclave
from legion.k8s.definitions import \
    LEGION_COMPONENT_LABEL, LEGION_COMPONENT_NAME_MODEL, \
    ENCLAVE_NAMESPACE_LABEL, LEGION_SYSTEM_LABEL, LEGION_SYSTEM_VALUE

LOGGER = logging.getLogger(__name__)
CONNECTION_CONTEXT = None


class ResourceWatch:
    """
    Watch for K8S resources (context manager)
    """

    def __init__(self, api_function, *args,
                 filter_callable=None,
                 object_constructor=None,
                 **kwargs):
        """
        Initialize context manager for resource watch

        :param api_function: API function to watch
        :param args: additional positional arguments for API function
        :param filter_callable: (Optional) callable to filter objects
        :param object_constructor:  (Optional) callable to construct object wrappers
        :param kwargs: additional key value arguments for API function
        """
        self._api_function = api_function
        self._filter_callable = filter_callable
        self._object_constructor = object_constructor
        self._args = args
        self._kwargs = kwargs

        self._watch = kubernetes.watch.Watch()
        self._stream = None

    def __enter__(self):
        """
        Enter watch

        :return:
        """
        self._stream = self._watch.stream(self._api_function,
                                          *self._args,
                                          **self._kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit watch

        :param exc_type: exception type
        :param exc_val: exception
        :param exc_tb: exception traceback
        :return: None
        """
        self.stop()

    @property
    def stream(self):
        """
        Access watch stream

        :return: tuple(str, Any) -- event type and event object (plain or constructed if
                                    object_constructor has been passed)
        """
        LOGGER.debug('Starting watch stream')

        reconnect = True
        while reconnect:
            reconnect = False

            try:
                for event in self._stream:
                    event_type = event['type']
                    event_object = event['object']

                    # Check if valid object
                    pass_event = not self._filter_callable or self._filter_callable(event_object)

                    if pass_event:
                        # Construct specific object
                        if self._object_constructor:
                            event_object = self._object_constructor(event_object)

                        yield (event_type, event_object)
            except urllib3.exceptions.ProtocolError:
                LOGGER.info('Connection to K8S API has been lost, reconnecting..')
                reconnect = True

        LOGGER.debug('Watch stream has been ended')

    @property
    def watch(self):
        """
        Access watch object

        :return: :py:class:`kubernetes.watch.Watch` -- watch object
        """
        return self._watch

    def stop(self):
        """
        Stop watch

        :return: None
        """
        try:
            self.watch.stop()
        finally:
            LOGGER.debug('Watch has been stopped')


def build_client():
    """
    Configure and returns kubernetes client

    :return: :py:module:`kubernetes.client`
    """
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.config_exception.ConfigException:
        kubernetes.config.load_kube_config(context=CONNECTION_CONTEXT)

    # Disable SSL warning for self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return kubernetes.client.ApiClient()


def get_current_namespace():
    """
    Get current namespace [WORKS ONLY IN-CLUSTER]

    :return: str -- name of namespace
    """
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as namespace_file:
            return namespace_file.read()
    except Exception as exception:
        raise Exception('Cannot get current namespace (it works only in cluster): {}'.format(exception))


def load_config(path_to_config):
    """
    Load cluster config

    :param path_to_config: path to cluster config file
    :type path_to_config: str
    :return: dict -- cluster config
    """
    if not os.path.exists(path_to_config):
        raise Exception('config path %s not exists' % path_to_config)

    if not os.path.isfile(path_to_config):
        raise Exception('config path %s is not a file' % path_to_config)

    with open(path_to_config, 'r') as stream:
        return yaml.load(stream)


def load_secrets(path_to_secrets):
    """
    Load all secrets from folder to dict

    :param path_to_secrets: path to secrets directory
    :type path_to_secrets: str
    :return: dict[str, str] -- dict of secret name => secret value
    """
    if not os.path.exists(path_to_secrets):
        raise Exception('secrets path %s not exists' % path_to_secrets)

    if not os.path.isdir(path_to_secrets):
        raise Exception('secrets path %s is not a directory' % path_to_secrets)

    files = [
        (file, os.path.abspath(os.path.join(path_to_secrets, file))) for file
        in os.listdir(path_to_secrets)
        if os.path.isfile(os.path.join(path_to_secrets, file))
    ]

    secrets = {}

    for name, path in files:
        try:
            with open(path, 'r') as stream:
                secrets[name] = stream.read()
                if isinstance(secrets[name], bytes):
                    secrets[name] = secrets[name].decode('utf-8')
        except IOError:
            pass
    return secrets


def find_model_deployment(model_id, namespace='default'):
    """
    Find model deployment by model id

    :param model_id: model id
    :type model_id: str
    :param namespace: namespace
    :type namespace: str
    :return: :py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    all_deployments = extension_api.list_namespaced_deployment(namespace)

    type_label_name = normalize_name(legion.containers.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_id_name = normalize_name(legion.containers.headers.DOMAIN_MODEL_ID)
    model_id_value = normalize_name(model_id)

    for deployment in all_deployments.items:
        if deployment.metadata.labels.get(type_label_name) == type_label_value \
                and deployment.metadata.labels.get(model_id_name) == model_id_value:
            return deployment

    return None


def find_all_models_deployments(namespace='default'):
    """
    Find all models deployments

    :param namespace: namespace
    :type namespace: str or none for all
    :return: list[:py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`]
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    if namespace:
        all_deployments = extension_api.list_namespaced_deployment(namespace)
    else:
        all_deployments = extension_api.list_deployment_for_all_namespaces()

    type_label_name = normalize_name(legion.containers.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_deployments = [
        deployment
        for deployment in all_deployments.items
        if deployment.metadata.labels.get(type_label_name) == type_label_value
    ]

    return model_deployments


def find_all_services(namespace='', component=''):
    """
    Find all services details by criteria

    :param namespace: namespace
    :type namespace: str or none for all
    :param component: filter by specified component value, or none for all
    :type component: str
    :return: list[V1Service]
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    if namespace:
        all_services = core_api.list_namespaced_service(namespace)
    else:
        all_services = core_api.list_service_for_all_namespaces()

    if component:
        all_services = [
            service
            for service in all_services.items
            if service.metadata.labels.get(LEGION_COMPONENT_LABEL) == component
        ]
    else:
        all_services = all_services.items

    return all_services


def get_service(namespace='', component=''):
    """
    Get a service details by criteria

    :param namespace: namespace
    :type namespace: str or none
    :param component: filter by specified component value, or none for all
    :type component: str
    :return: V1Service or None
    """
    result = find_all_services(namespace, component)
    return legion.k8s.services.Service(result[0]) if result else None


def find_all_ingresses(namespace='', component=''):
    """
    Find all ingresses details by criteria

    :param namespace: namespace
    :type namespace: str or none for all
    :type component: filter by specified component value, or none for all
    :return: list[V1beta1Ingress]
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    if namespace:
        all_ingresses = extension_api.list_namespaced_ingress(namespace)
    else:
        all_ingresses = extension_api.list_ingress_for_all_namespaces()

    if component:
        all_ingresses = [
            ingress
            for ingress in all_ingresses.items
            if ingress.metadata.labels.get(LEGION_COMPONENT_LABEL) == component
        ]
    else:
        all_ingresses = all_ingresses.items

    return all_ingresses


def get_ingress(namespace='', component=''):
    """
    Get ingress details by criteria

    :param namespace: namespace
    :type namespace: str or none for all
    :type component: filter by specified component value, or none for all
    :return: V1beta1Ingress -- Ingress object or None
    """
    ingresses = find_all_ingresses(namespace, component)
    return ingresses[0] if ingresses else None


def get_ingress_url(ingress):
    """
    Get URL of ingress object

    :param ingress: ingress object
    :type ingress: V1beta1Ingress
    :return: str or None -- URL from tls section,
    """
    spec = ingress.spec

    host = spec.rules[0].host if spec.rules else None
    if not host:
        return None

    protocol = 'https' if spec.tls and any(host in tls.hosts for tls in spec.tls) else 'http'

    return '{}://{}'.format(protocol, host)


def get_docker_image_labels(image):
    """
    Get labels from docker image

    :param image: docker image
    :type image: str
    :return: dict[str, Any] -- image labels
    """
    docker_client = legion.containers.docker.build_docker_client(None)
    try:
        try:
            docker_image = docker_client.images.get(image)
        except docker.errors.ImageNotFound:
            docker_image = docker_client.images.pull(image)
    except Exception as docker_pull_exception:
        raise Exception('Cannot pull docker image {}: {}'.format(image, docker_pull_exception))

    required_headers = [
        legion.containers.headers.DOMAIN_MODEL_ID,
        legion.containers.headers.DOMAIN_MODEL_VERSION,
        legion.containers.headers.DOMAIN_CONTAINER_TYPE
    ]

    if any(header not in docker_image.labels for header in required_headers):
        raise Exception('Missed one of %s labels. Available labels: %s' % (
            ', '.join(required_headers),
            ', '.join(tuple(docker_image.labels.keys()))
        ))

    return docker_image.labels


def get_meta_from_docker_labels(labels):
    """
    Build meta fields for kubernetes from docker labels.

    :param labels: docker image labels
    :type labels: dict[str, Any]
    :return: tuple[str, dict[str, str], str, str] -- k8s_name name, labels in DNS-1123 format, model id and version
    """
    model_id = labels[legion.containers.headers.DOMAIN_MODEL_ID]
    model_version = labels[legion.containers.headers.DOMAIN_MODEL_VERSION]

    k8s_name = "model-%s-%s" % (
        normalize_name(model_id),
        normalize_name(model_version)
    )

    compatible_labels = {
        normalize_name(k): normalize_name(v)
        for k, v in
        labels.items()
    }

    compatible_labels[LEGION_COMPONENT_LABEL] = LEGION_COMPONENT_NAME_MODEL
    compatible_labels[LEGION_SYSTEM_LABEL] = LEGION_SYSTEM_VALUE

    return normalize_name(k8s_name, dns_1035=True), compatible_labels, model_id, model_version


def find_enclaves():
    """
    Get a list of enclaves

    :return list[Enclave] -- list of found enclaves
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    all_namespaces = core_api.list_namespace()

    enclaves = []
    for namespace in all_namespaces.items:
        if namespace.metadata.labels and ENCLAVE_NAMESPACE_LABEL in namespace.metadata.labels:
            enclaves.append(legion.k8s.enclave.Enclave(namespace.metadata.name))

    return enclaves
