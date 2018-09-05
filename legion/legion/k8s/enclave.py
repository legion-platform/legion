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
import legion.k8s.watch
import legion.k8s.utils
import legion.k8s.services
import legion.k8s.properties
import legion.utils

LOGGER = logging.getLogger(__name__)

SERVE_HEALTH_CHECK = '/healthcheck'


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

        self._edi_service = legion.k8s.services.get_service(self.name, LEGION_COMPONENT_NAME_EDI)
        self._api_service = legion.k8s.services.get_service(self.name, LEGION_COMPONENT_NAME_API)
        self._grafana_service = legion.k8s.services.get_service(self.name, LEGION_COMPONENT_NAME_GRAFANA)
        self._graphite_service = legion.k8s.services.get_service(self.name, LEGION_COMPONENT_NAME_GRAPHITE)

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
        for service in legion.k8s.services.find_all_services(namespace=self.name):
            if legion.k8s.services.ModelService.is_model_service(service):
                model_service = legion.k8s.services.ModelService(service)
                models[model_service.id_and_version] = model_service
        return models

    def get_models(self, model_id=None, model_version=None):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)

        :param model_id: model id or */None for all models
        :type model_id: str or None
        :param model_version: (Optional) model version or */None for all
        :type model_version: str or None
        :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
        """
        return [
            model_service
            for id_and_version, model_service in self.models.items()
            if model_id in (id_and_version.id, '*', None) and model_version in (id_and_version.version, None, '*')
        ]

    def get_models_strict(self, model_id, model_version=None, ignore_not_found=False):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)
        If more that one model would be found with unstrict criterion - exception would be raised
        If no one model would be found - exception would be raised

        param model_id: model id or * for all models
        :type model_id: str
        :param model_version: (Optional) model version
        :type model_version: str
        :param ignore_not_found: (Optional) ignore exception if cannot find any model
        :type ignore_not_found: bool
        :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
        """
        model_services = self.get_models(model_id, model_version)

        ignore_strictness = model_id == '*' or model_version == '*'

        if len(model_services) > 1:
            LOGGER.info('More than one model was found for filter: id={!r} version={!r}'
                        .format(model_id, model_version))
            if not ignore_strictness and not model_version:
                raise Exception('Please specify version of model')

        if not model_services:
            if not ignore_not_found:
                raise Exception('No one model can be found')
            else:
                LOGGER.info('Cannot find any model - ignoring due to ignore-not-found parameter')

        return model_services

    def _validate_model_properties_storage(self, model_id, model_version, default_values):
        """
        Validate that model properties for model exists in a cluster and contains required properties
        If there are not properties storage in a cluster - create with default values

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param default_values: default values for properties
        :type default_values: dict[str, str]
        :return: None
        """
        properties = default_values.keys()
        if not properties:  # if model does not require properties check can be omitted
            LOGGER.info('Skipping model {!r} properties analyzing due they are not presented')
            return

        registered_storages = legion.k8s.properties.K8SConfigMapStorage.list(self.namespace)
        storage_name = legion.utils.model_properties_storage_name(model_id, model_version)
        storage = legion.k8s.K8SConfigMapStorage(storage_name, self.namespace)

        LOGGER.info('Found properties storages: {!r}. Checking storage name {!r}'.format(registered_storages,
                                                                                         storage_name))

        if storage_name in registered_storages:
            LOGGER.info('Analyzing properties storage {!r} for model {!r}'.format(storage, model_id))
            storage.load()

            storage_keys = set(storage.keys())
            LOGGER.info('Storage already has keys: {!r}'.format(storage_keys))

            missed_properties = set(properties) - storage_keys
            if missed_properties:
                LOGGER.info('Storage has missed properties: {!r}'.format(missed_properties))

                for missed_property in missed_properties:
                    storage[missed_property] = default_values[missed_property]
                    LOGGER.info('Property {!r} has been set to default value {!r}'
                                .format(missed_property, default_values[missed_property]))
        else:
            LOGGER.info('Creating properties storage {!r} for model {!r} with default values'.format(storage, model_id))
            for k, v in default_values.items():
                storage[k] = v
                LOGGER.info('Property {!r} has been set to default value {!r}'.format(k, v))
                storage.save()

    def deploy_model(self, image, count=1, livenesstimeout=2, readinesstimeout=2):
        """
        Deploy new model

        :param image: docker image with model
        :type image: str
        :param count: count of pods
        :type count: int
        :param livenesstimeout: model pod startup timeout (used in liveness probe)
        :type livenesstimeout: int
        :param readinesstimeout: model pod startup timeout (used readiness probe)
        :type readinesstimeout: int
        :return: :py:class:`legion.k8s.services.ModelService` -- model service
        """
        if count < 1:
            raise Exception('Invalid scale parameter: should be greater then 0')

        client = legion.k8s.utils.build_client()
        LOGGER.info('Gathering docker labels from image {}'.format(image))
        labels = legion.k8s.utils.get_docker_image_labels(image)
        image_meta_information = legion.k8s.utils.get_meta_from_docker_labels(labels)
        LOGGER.info('{} has been gathered from image {}'.format(image_meta_information, image))

        model_properties_default_values_str = labels.get(legion.containers.headers.DOMAIN_MODEL_PROPERTY_VALUES)
        model_properties_default_values = legion.k8s.properties.K8SPropertyStorage.parse_data_from_string(
            model_properties_default_values_str
        )

        self._validate_model_properties_storage(
            image_meta_information.model_id,
            image_meta_information.model_version,
            model_properties_default_values
        )

        if self.get_models(image_meta_information.model_id, image_meta_information.model_version):
            raise Exception('Duplicating model id and version (id={}, version={})'
                            .format(image_meta_information.model_id, image_meta_information.model_version))

        # REFACTOR, maybe we should remove that
        container_env_variables = {
            legion.config.STATSD_HOST[0]: self.graphite_service.internal_domain,
            legion.config.STATSD_PORT[0]: str(self.graphite_service.internal_port)
        }

        http_get_object = kubernetes.client.V1HTTPGetAction(
            path='/healthcheck',
            port=legion.config.LEGION_PORT[1]
            )

        livenessprobe = kubernetes.client.V1Probe(
            failure_threshold=10,
            http_get=http_get_object,
            initial_delay_seconds=livenesstimeout,
            period_seconds=10,
            timeout_seconds=2
        )

        readinessprobe = kubernetes.client.V1Probe(
            failure_threshold=5,
            http_get=http_get_object,
            initial_delay_seconds=readinesstimeout,
            period_seconds=10,
            timeout_seconds=2
        )

        container = kubernetes.client.V1Container(
            name='model',
            image=image,
            image_pull_policy='Always',
            env=[
                kubernetes.client.V1EnvVar(name=k, value=str(v))
                for k, v in container_env_variables.items()
            ],
            liveness_probe=livenessprobe,
            readiness_probe=readinessprobe,
            ports=[
                kubernetes.client.V1ContainerPort(container_port=legion.config.LEGION_PORT[1],
                                                  name='api', protocol='TCP')
            ])

        pod_template = kubernetes.client.V1PodTemplateSpec(
            metadata=kubernetes.client.V1ObjectMeta(annotations=image_meta_information.kubernetes_annotations,
                                                    labels=image_meta_information.kubernetes_labels),
            spec=kubernetes.client.V1PodSpec(
                containers=[container],
                service_account_name=legion.config.MODEL_INSTANCE_SERVICE_ACCOUNT_NAME
            ))

        deployment_spec = kubernetes.client.ExtensionsV1beta1DeploymentSpec(
            replicas=count,
            template=pod_template)

        deployment = kubernetes.client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=kubernetes.client.V1ObjectMeta(name=image_meta_information.k8s_name,
                                                    annotations=image_meta_information.kubernetes_annotations,
                                                    labels=image_meta_information.kubernetes_labels),
            spec=deployment_spec)

        extensions_v1beta1 = kubernetes.client.ExtensionsV1beta1Api(client)

        LOGGER.info('Creating deployment {} in namespace {}'.format(image_meta_information.k8s_name,
                                                                    self.namespace))
        extensions_v1beta1.create_namespaced_deployment(
            body=deployment,
            namespace=self.namespace)

        # Creating a service
        service_spec = kubernetes.client.V1ServiceSpec(
            selector=image_meta_information.kubernetes_labels,
            ports=[kubernetes.client.V1ServicePort(name='api', protocol='TCP', port=5000, target_port='api')])

        service = kubernetes.client.V1Service(
            api_version='v1',
            kind='Service',
            metadata=kubernetes.client.V1ObjectMeta(name=image_meta_information.k8s_name,
                                                    annotations=image_meta_information.kubernetes_annotations,
                                                    labels=image_meta_information.kubernetes_labels),
            spec=service_spec)

        core_v1api = kubernetes.client.CoreV1Api(client)

        LOGGER.info('Creating service {} in namespace {}'.format(image_meta_information.k8s_name,
                                                                 self.namespace))
        k8s_service = core_v1api.create_namespaced_service(
            body=service,
            namespace=self.namespace)

        LOGGER.info('Building model service object')
        return legion.k8s.services.ModelService(k8s_service)

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

        watch = legion.k8s.watch.ResourceWatch(core_api.list_namespaced_service,
                                               namespace=self.namespace,
                                               filter_callable=legion.k8s.services.Service.is_legion_service,
                                               object_constructor=legion.k8s.services.Service)
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

        watch = legion.k8s.watch.ResourceWatch(core_api.list_namespace,
                                               filter_callable=Enclave.is_enclave,
                                               object_constructor=Enclave.build_from_namespace_object)

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


def find_enclaves():
    """
    Get a list of enclaves

    :return list[Enclave] -- list of found enclaves
    """
    client = legion.k8s.utils.build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    all_namespaces = core_api.list_namespace()

    enclaves = []
    for namespace in all_namespaces.items:
        if namespace.metadata.labels and ENCLAVE_NAMESPACE_LABEL in namespace.metadata.labels:
            enclaves.append(legion.k8s.enclave.Enclave(namespace.metadata.name))

    return enclaves
