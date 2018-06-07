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
legion k8s enclave class
"""
import logging
import os

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import urllib3.exceptions

import legion.containers.headers
import legion.config
from legion.k8s.definitions import ENCLAVE_NAMESPACE_LABEL
from legion.k8s.definitions import \
    LEGION_COMPONENT_NAME_API, LEGION_COMPONENT_NAME_EDI, \
    LEGION_COMPONENT_NAME_GRAFANA, LEGION_COMPONENT_NAME_GRAPHITE
import legion.k8s.utils
import legion.k8s.services
import legion.utils

LOGGER = logging.getLogger(__name__)


class Enclave:
    """
    Contains overall information about enclave, its services and models
    """

    def __init__(self, name):
        """
        Create an Enclave instance

        :param name: enclave name
        """
        self._name = name

        self._data_loaded = False

        self._edi_service = None
        self._api_service = None
        self._grafana_service = None
        self._graphite_service = None

    @staticmethod
    def build_from_namespace_object(ns_object):
        """
        Build Enclave from namespace object

        :param ns_object: namespace object
        :return: :py:class:`Enclave` -- enclave
        """
        return Enclave(ns_object.metadata.name)

    @staticmethod
    def is_enclave(namespace):
        """
        Is specific K8S namespace is K8S namespace

        :param namespace: K8S namespace
        :return: bool - is namespace is enclave namespace
        """
        return namespace.metadata.labels and ENCLAVE_NAMESPACE_LABEL in namespace.metadata.labels

    def __repr__(self):
        """
        Return representation of object

        :return: str -- string representation
        """
        return 'Enclave({!r})'.format(self._name)

    def _load_services(self):
        """
        Load all services data (lazy loading)

        :return: None
        """
        if self._data_loaded:
            return

        self._data_loaded = True

        self._edi_service = legion.k8s.utils.get_service(self.name, LEGION_COMPONENT_NAME_EDI)
        self._api_service = legion.k8s.utils.get_service(self.name, LEGION_COMPONENT_NAME_API)
        self._grafana_service = legion.k8s.utils.get_service(self.name, LEGION_COMPONENT_NAME_GRAFANA)
        self._graphite_service = legion.k8s.utils.get_service(self.name, LEGION_COMPONENT_NAME_GRAPHITE)

    @property
    def name(self):
        """
        Return enclave name, currently it equals to K8s namespace name

        :return: str -- enclave name
        """
        return self._name

    @property
    def namespace(self):
        """
        Return enclave namespace, currently it equals to enclave name

        :return: str -- enclave namespace
        """
        return self._name

    @property
    def edi_service(self):
        """
        Return EDI service object.

        :return: :py:class:`legion.k8s.Service` -- EDI service object or None
        """
        self._load_services()
        return self._edi_service

    @property
    def api_service(self):
        """
        Return model API service object (previously known as EDGE).

        :return: :py:class:`legion.k8s.Service` -- api service object or None
        """
        self._load_services()
        return self._api_service

    @property
    def grafana_service(self):
        """
        Return Grafana service object.

        :return: :py:class:`legion.k8s.Service` -- Grafana service object or None
        """
        self._load_services()
        return self._grafana_service

    @property
    def graphite_service(self):
        """
        Return Graphite service object.

        :return: :py:class:`legion.k8s.Service` -- Graphite service object or None
        """
        self._load_services()
        return self._graphite_service

    @property
    def models(self):
        """
        Return a dict of Models services.

        :return: dict[:py:class:`legion.k8s.ModelIdVersion`, :py:class:`legion.k8s.ModelService`] -- deployed models
        """
        models = {}
        for service in legion.k8s.utils.find_all_services(namespace=self.name):
            if legion.k8s.services.ModelService.is_model_service(service):
                model_service = legion.k8s.services.ModelService(service)
                models[model_service.id_and_version] = model_service
        return models

    def get_models(self, model_id, model_version=None):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)

        :param model_id: model id or * for all models
        :type model_id: str
        :param model_version: (Optional) model version or * for all
        :type model_version: str
        :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
        """
        return [
            model_service
            for id_and_version, model_service in self.models.items()
            if model_id in (id_and_version.id, '*') and model_version in (id_and_version.version, None, '*')
        ]

    def get_models_strict(self, model_id, model_version=None):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)
        If more that one model would be found with unstrict criterion - exception would be raised
        If no one model would be found - exception would be raised

        param model_id: model id or * for all models
        :type model_id: str
        :param model_version: (Optional) model version
        :type model_version: str
        :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
        """
        model_services = self.get_models(model_id, model_version)

        if len(model_services) > 1 and not model_version:
            raise Exception('Please specify version of model')

        if not model_services:
            raise Exception('No one model can be found')

        return model_services

    def deploy_model(self, image, count=1):
        """
        Deploy new model

        :param image: docker image with model
        :type image: str
        :param count: count of pods
        :type count: int
        :return: :py:class:`legion.k8s.services.ModelService` -- model service
        """
        client = legion.k8s.utils.build_client()

        introspection_image = image

        if os.getenv('EXTERNAL_TEST') and '-local' in introspection_image:
            introspection_image = introspection_image.replace('-local', '')

        labels = legion.k8s.utils.get_docker_image_labels(introspection_image)
        k8s_name, compatible_labels, model_id, model_version = legion.k8s.utils.get_meta_from_docker_labels(labels)

        if self.get_models(model_id, model_version):
            raise Exception('Cannot deploy second model with id={} and version={}'.format(model_id, model_version))

        container_env_variables = {
            legion.config.STATSD_HOST[0]: self.graphite_service.internal_domain,
            legion.config.STATSD_PORT[0]: str(self.graphite_service.internal_port)
        }

        container = kubernetes.client.V1Container(
            name='model',
            image=image,
            image_pull_policy='Always',
            env=[
                kubernetes.client.V1EnvVar(name=k, value=str(v))
                for k, v in container_env_variables.items()
            ],
            ports=[kubernetes.client.V1ContainerPort(container_port=5000, name='api', protocol='TCP')])

        template = kubernetes.client.V1PodTemplateSpec(
            metadata=kubernetes.client.V1ObjectMeta(labels=compatible_labels),
            spec=kubernetes.client.V1PodSpec(containers=[container]))

        deployment_spec = kubernetes.client.ExtensionsV1beta1DeploymentSpec(
            replicas=count,
            template=template)

        deployment = kubernetes.client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=kubernetes.client.V1ObjectMeta(name=k8s_name, labels=compatible_labels),
            spec=deployment_spec)

        extensions_v1beta1 = kubernetes.client.ExtensionsV1beta1Api(client)

        LOGGER.info('Creating deployment {} in namespace {}'.format(k8s_name, self.namespace))
        extensions_v1beta1.create_namespaced_deployment(
            body=deployment,
            namespace=self.namespace)

        # Creating a service
        core_v1api = kubernetes.client.CoreV1Api(client)

        service_selector = {k: v for k, v in compatible_labels.items()
                            if k in [legion.containers.headers.DOMAIN_MODEL_ID,
                                     legion.containers.headers.DOMAIN_MODEL_VERSION]}

        service_spec = kubernetes.client.V1ServiceSpec(
            selector=service_selector,
            ports=[kubernetes.client.V1ServicePort(name='api', protocol='TCP', port=5000, target_port='api')])

        service = kubernetes.client.V1Service(
            api_version='v1',
            kind='Service',
            metadata=kubernetes.client.V1ObjectMeta(name=k8s_name, labels=compatible_labels),
            spec=service_spec)

        LOGGER.info('Creating service {} in namespace {}'.format(k8s_name, self.namespace))
        core_v1api.create_namespaced_service(
            body=service,
            namespace=self.namespace)

        model_services = self.get_models(model_id, model_version)
        if model_services:
            return model_services[0]
        else:
            raise Exception('Cannot find created model service for model {} id {}'.format(model_id, model_version))

    def watch_models(self):
        """
        Watch for models update events in this Enclave object

        :return: (str, :py:class:`legion.k8s.services.ModelService`) -- (event type [ADDED, DELETED, MODIFIED], model)
        """
        for event_type, service in self.watch_services():
            if legion.k8s.services.ModelService.is_model_service(service.k8s_service):
                model_service = legion.k8s.services.ModelService(service.k8s_service)
                yield (event_type, model_service)

    def watch_model_service_endpoints_state(self):
        """
        Watch for model service endpoints state

        :return: (list[:py:class:`legion.k8s.services.ModelServiceEndpoint`] -- new version of model service endpoints
        """
        endpoints = set()

        def normalize_endpoints(endpoints_to_normalize):
            """
            Normalize endpoints set to list with default endpoints for each models

            :param endpoints_to_normalize: source model endpoints
            :type endpoints_to_normalize: set[:py:class:`legion.k8s.services.ModelServiceEndpoint`]
            :return list[:py:class:`legion.k8s.services.ModelServiceEndpoint`] -- endpoints with default
            """
            result = []
            default_endpoints_models = {}

            for endpoint in endpoints_to_normalize:
                model_id = endpoint.model_service.id

                # TODO: Change in future, add default model choosing algorithm
                default_endpoints_models[model_id] = endpoint
                result.append(endpoint)

            # Append defaults to the end
            for default_endpoint in default_endpoints_models.values():
                result.append(default_endpoint.build_default())

            return result

        for (event_type, model_service) in self.watch_models():
            model_endpoint = legion.k8s.services.ModelServiceEndpoint(model_service)

            if event_type == legion.k8s.EVENT_ADDED:
                endpoints.add(model_endpoint)
            elif event_type == legion.k8s.EVENT_MODIFIED:
                endpoints.add(model_endpoint)
            elif event_type == legion.k8s.EVENT_DELETED:
                if model_endpoint in endpoints:
                    endpoints.remove(model_endpoint)
            else:
                LOGGER.error('Got unknown event type: {}'.format(event_type))

            yield normalize_endpoints(endpoints)

    def watch_services(self):
        """
        Generate which returns events for services updates

        :return: (str, :py:class:`legion.k8s.services.Service`) -- (event type [ADDED, DELETED, MODIFIED], service)
        """
        client = legion.k8s.utils.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        with legion.k8s.utils.ResourceWatch(core_api.list_namespaced_service,
                                            namespace=self.namespace,
                                            filter_callable=legion.k8s.services.Service.is_legion_service,
                                            object_constructor=legion.k8s.services.Service) as watch:
            for (event_type, event_object) in watch.stream:
                yield (event_type, event_object)

    @staticmethod
    def watch_enclaves():
        """
        Generate which returns events for enclaves

        :return: A tuple (event type [ADDED, DELETED, MODIFIED], service object)
        :rtype: (str, Enclave)
        """
        client = legion.k8s.utils.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        with legion.k8s.utils.ResourceWatch(core_api.list_namespace,
                                            filter_callable=Enclave.is_enclave,
                                            object_constructor=Enclave.build_from_namespace_object) as watch:
            for (event_type, event_object) in watch.stream:
                yield (event_type, event_object)

    def delete(self, grace_period_seconds=0):
        """
        Delete enclave

        :param grace_period_seconds: grace period in seconds
        :type grace_period_seconds: int
        :return: None
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        body = kubernetes.client.V1DeleteOptions(propagation_policy='Foreground',
                                                 grace_period_seconds=grace_period_seconds)

        core_api.delete_namespace(self.name, body)
