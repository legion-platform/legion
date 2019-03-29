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
from collections import Counter

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
from kubernetes.client import V1ResourceRequirements

from legion.sdk import config
from legion.services.k8s import utils as k8s_utils, services
from legion.sdk.definitions import ENCLAVE_NAMESPACE_LABEL, EVENT_ADDED, EVENT_MODIFIED, EVENT_DELETED
from legion.sdk.definitions import \
    LEGION_COMPONENT_NAME_API, LEGION_COMPONENT_NAME_EDI
from legion.services.k8s.exceptions import KubernetesOperationIsNotConfirmed
from legion.services.k8s.services import get_service, ModelService, find_model_services_by, find_model_service, \
    find_model_deployment, ModelServiceEndpoint, Service
from legion.services.k8s.watch import ResourceWatch
from legion.sdk.utils import ensure_function_succeed

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

        self._edi_service = get_service(self.name, LEGION_COMPONENT_NAME_EDI)
        self._api_service = get_service(self.name, LEGION_COMPONENT_NAME_API)

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

    def get_models(self, model_id=None, model_version=None):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)

        :param model_id: model id or */None for all models
        :type model_id: str or None
        :param model_version: (Optional) model version or */None for all
        :type model_version: str or None
        :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
        """
        items = [ModelService(service) for service in
                 find_model_services_by(self.name, model_id, model_version)]

        return sorted(items, key=lambda ms: '{}/{}'.format(ms.id, ms.version))

    def get_model(self, model_id, model_version):
        """
        Get model by model id and model version. Return None if there is no the model

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :return: Optional[:py:class:`legion.k8s.ModelService`] -- founded model service
        """
        service = find_model_service(self.name, model_id, model_version)

        return ModelService(service) if service else None

    def get_models_strict(self, model_id, model_version=None, ignore_not_found=False):
        """
        Get models that fit match criterions (model id and model version, model id may be *, model version may be *)
        If more that one model would be found with unstrict criterion - exception would be raised
        If no one model would be found - exception would be raised

        :param model_id: model id or * for all models
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

    def deploy_model(self, image, model_iam_role=None, count=1, livenesstimeout=2, readinesstimeout=2, memory=None,
                     cpu=None):
        """
        Deploy new model. Return True if model is deployed

        :param image: docker image with model
        :type image: str
        :param model_iam_role: IAM role to be used at model pod
        :type model_iam_role: str
        :param count: count of pods
        :type count: int
        :param livenesstimeout: model pod startup timeout (used in liveness probe)
        :type livenesstimeout: int
        :param readinesstimeout: model pod startup timeout (used readiness probe)
        :type readinesstimeout: int
        :param memory: limit memory for model deployment
        :type memory: str
        :param cpu: limit cpu for model deployment
        :type cpu: str
        :return: (bool, :py:class:`legion.k8s.services.ModelService`) -- model service
        """
        if count < 1:
            raise Exception('Invalid scale parameter: should be greater then 0')

        client = k8s_utils.build_client()

        LOGGER.info('Gathering docker labels from image {}'.format(image))
        labels = k8s_utils.get_docker_image_labels(image)

        image_meta_information = k8s_utils.get_meta_from_docker_labels(labels)
        LOGGER.info('{} has been gathered from image {}'.format(image_meta_information, image))

        model = self.get_model(image_meta_information.model_id, image_meta_information.model_version)
        if model:
            LOGGER.info('Same model already has been deployed - skipping')

            return False, model

        http_get_object = kubernetes.client.V1HTTPGetAction(
            path='/healthcheck',
            port=config.LEGION_PORT
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

        cpu = cpu or config.MODEL_K8S_CPU
        memory = memory or config.MODEL_K8S_MEMORY

        resources = V1ResourceRequirements(
            limits={'cpu': cpu, 'memory': memory},
            requests={'cpu': k8s_utils.reduce_cpu_resource(cpu), 'memory': k8s_utils.reduce_mem_resource(memory)}
        )

        container = kubernetes.client.V1Container(
            name='model',
            image=image,
            resources=resources,
            liveness_probe=livenessprobe,
            readiness_probe=readinessprobe,
            ports=[
                kubernetes.client.V1ContainerPort(container_port=config.LEGION_PORT,
                                                  name='api', protocol='TCP')
            ])

        pod_annotations = image_meta_information.kubernetes_annotations
        pod_annotations['iam.amazonaws.com/role'] = model_iam_role

        pod_template = kubernetes.client.V1PodTemplateSpec(
            metadata=kubernetes.client.V1ObjectMeta(annotations=pod_annotations,
                                                    labels=image_meta_information.kubernetes_labels),
            spec=kubernetes.client.V1PodSpec(
                containers=[container],
                service_account_name=config.MODEL_INSTANCE_SERVICE_ACCOUNT_NAME
            ))

        deployment_spec = kubernetes.client.V1DeploymentSpec(
            replicas=count,
            template=pod_template,
            selector=kubernetes.client.V1LabelSelector(
                match_labels=image_meta_information.kubernetes_labels))

        deployment = kubernetes.client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=kubernetes.client.V1ObjectMeta(name=image_meta_information.k8s_name,
                                                    annotations=pod_annotations,
                                                    labels=image_meta_information.kubernetes_labels),
            spec=deployment_spec)

        apps_api = kubernetes.client.AppsV1Api(client)

        LOGGER.info('Creating deployment {} in namespace {}'.format(image_meta_information.k8s_name,
                                                                    self.namespace))
        apps_api.create_namespaced_deployment(
            body=deployment,
            namespace=self.namespace)

        retries = config.K8S_API_RETRY_NUMBER_MAX_LIMIT
        retry_timeout = config.K8S_API_RETRY_DELAY_SEC

        deployment_ready = ensure_function_succeed(
            lambda: find_model_deployment(self.name, image_meta_information.model_id,
                                          image_meta_information.model_version),
            retries, retry_timeout, boolean_check=True
        )

        if not deployment_ready:
            raise KubernetesOperationIsNotConfirmed(
                'Cannot create deployment {}'.format(image_meta_information.k8s_name)
            )

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

        service_ready = ensure_function_succeed(
            lambda: services.find_model_service(self.namespace,
                                                image_meta_information.model_id,
                                                image_meta_information.model_version),
            retries, retry_timeout, boolean_check=True
        )

        if not service_ready:
            raise KubernetesOperationIsNotConfirmed(
                'Cannot create service {}'.format(image_meta_information.k8s_name)
            )

        LOGGER.info('Building model service object')
        return True, ModelService(k8s_service)

    def watch_models(self):
        """
        Watch for models update events in this Enclave object

        :return: (str, :py:class:`legion.k8s.services.ModelService`) -- (event type [ADDED, DELETED, MODIFIED], model)
        """
        for event_type, service in self.watch_services():
            if ModelService.is_model_service(service.k8s_service):
                model_service = ModelService(service.k8s_service)
                yield event_type, model_service

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
            model_endpoints = []
            unspecified_version_endpoints = {}
            model_id_counter = Counter(x.model_service.id for x in endpoints_to_normalize)

            for endpoint in endpoints_to_normalize:
                model_id = endpoint.model_service.id
                model_endpoints.append(endpoint)

                if model_id_counter[model_id] == 1:
                    model_endpoints.append(endpoint.build_default())
                else:
                    unspecified_version_endpoints[model_id] = endpoint.build_default()

            return model_endpoints, list(unspecified_version_endpoints.values())

        for event_type, model_service in self.watch_models():
            model_endpoint = ModelServiceEndpoint(model_service)

            if event_type == EVENT_ADDED:
                endpoints.add(model_endpoint)
            elif event_type == EVENT_MODIFIED:
                endpoints.add(model_endpoint)
            elif event_type == EVENT_DELETED:
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
        client = k8s_utils.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        watch = ResourceWatch(core_api.list_namespaced_service,
                              namespace=self.namespace,
                              filter_callable=Service.is_legion_service,
                              object_constructor=Service)
        for event_type, event_object in watch.stream:
            yield event_type, event_object

    @staticmethod
    def watch_enclaves():
        """
        Generate which returns events for enclaves

        :return: A tuple (event type [ADDED, DELETED, MODIFIED], service object)
        :rtype: (str, Enclave)
        """
        client = k8s_utils.build_client()

        core_api = kubernetes.client.CoreV1Api(client)

        watch = ResourceWatch(core_api.list_namespace,
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
        client = k8s_utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        body = kubernetes.client.V1DeleteOptions(propagation_policy='Foreground',
                                                 grace_period_seconds=grace_period_seconds)

        core_api.delete_namespace(self.name, body)


def find_enclaves():
    """
    Get a list of enclaves

    :return list[Enclave] -- list of found enclaves
    """
    client = k8s_utils.build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    all_namespaces = core_api.list_namespace()

    enclaves = []
    for namespace in all_namespaces.items:
        if namespace.metadata.labels and ENCLAVE_NAMESPACE_LABEL in namespace.metadata.labels:
            enclaves.append(Enclave(namespace.metadata.name))

    return enclaves
