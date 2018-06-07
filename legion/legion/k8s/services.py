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
legion k8s services classes
"""
import logging

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception

import legion.model
from legion.containers.headers import DOMAIN_MODEL_ID, DOMAIN_MODEL_VERSION
import legion.k8s.enclave
from legion.k8s.definitions import ModelIdVersion
from legion.k8s.definitions import LEGION_COMPONENT_LABEL, LEGION_SYSTEM_LABEL, LEGION_API_SERVICE_PORT
from legion.k8s.definitions import STATUS_OK, STATUS_WARN, STATUS_FAIL
import legion.k8s.utils

LOGGER = logging.getLogger(__name__)


class Service:
    """
    Data-structure for describing K8S service
    """

    def __init__(self, k8s_service):
        """
        Build service structure from K8S Service

        :param k8s_service: K8S service
        :type k8s_service: V1Service
        """
        if not k8s_service.metadata.labels:
            raise Exception('Cannot construct Service from K8S service without any labels')

        self._name = k8s_service.metadata.labels.get(LEGION_COMPONENT_LABEL)

        if not self._name:
            raise Exception('Cannot construct Service from K8S service without label {}'.format(LEGION_COMPONENT_LABEL))

        self._k8s_service = k8s_service
        # Get port
        ports = self.k8s_service.spec.ports
        if not ports:
            raise Exception('Service {} doesnt contain any port declaration'.format(self._name))

        api_ports = [port.port for port in ports if port.name == LEGION_API_SERVICE_PORT]
        if not api_ports:
            raise Exception('Cannot find api port (should be label with {}) for service {}'
                            .format(LEGION_API_SERVICE_PORT, self._name))

        self._port = api_ports[0]

        self._data_loaded = False

        self._public_url = None

    @property
    def k8s_service(self):
        """
        Get K8S service

        :return: V1Service -- K8S service
        """
        return self._k8s_service

    @staticmethod
    def is_legion_service(k8s_service):
        """
        Check that k8s service is legion service

        :param k8s_service: K8S service
        :type k8s_service: V1Service
        :return: bool -- is legion service
        """
        return k8s_service.metadata.labels and all(header in k8s_service.metadata.labels
                                                   for header in [LEGION_COMPONENT_LABEL, LEGION_SYSTEM_LABEL])

    def _load_data(self):
        """
        Load all required data (lazy loading)

        :return: None
        """
        if self._data_loaded:
            return

        self._ingress = legion.k8s.utils.get_ingress(self._k8s_service.metadata.namespace, self.name)
        if self._ingress:
            self._public_url = legion.k8s.utils.get_ingress_url(self._ingress)

        self._data_loaded = True

    def reload_cache(self):
        """
        Reload all cached data

        :return: None
        """
        self._data_loaded = False
        self._load_data()

    @property
    def name(self):
        """
        Get name of service (for example, edi)

        :return: str -- name of service
        """
        return self._name

    @property
    def public_url(self):
        """
        Get public http(s) URL for service (from linked ingress).
        HTTPS would be used if it configured in ingress

        :return: str or None -- public URL of service if service linked to ingress
        """
        self._load_data()
        return self._public_url

    @property
    def internal_domain(self):
        """
        Get internal domain

        :return: str -- internal domain
        """
        return '{}.{}'.format(self.k8s_service.metadata.name, self.k8s_service.metadata.namespace)

    @property
    def internal_port(self):
        """
        Get internal service port (if present)

        :return: int ot None -- internal port
        """
        return self._port

    @property
    def url(self):
        """
        Get internal URL for service

        :return: str -- internal URL
        """
        return 'http://{}:{}'.format(self.internal_domain, self._port)

    @property
    def namespace(self):
        """
        Get service namespace

        :return: str -- namespace
        """
        return self.k8s_service.metadata.namespace

    @property
    def enclave(self):
        """
        Get service enclave

        :return: :py:class:`legion.k8s.enclave.Enclave` -- enclave
        """
        return legion.k8s.enclave.Enclave(self.namespace)

    def __str__(self):
        """
        Get string representation

        :return: str
        """
        return 'Service for {}'.format(self.name)

    __repr__ = __str__


class ModelService(Service):
    """
    Data-structure for describing model service
    """

    def __init__(self, k8s_service):
        """
        Build model service structure from K8S Service

        :param k8s_service: K8S service
        :type k8s_service: V1Service
        """
        super().__init__(k8s_service)
        self._model_id = k8s_service.metadata.labels.get(DOMAIN_MODEL_ID)
        self._model_version = k8s_service.metadata.labels.get(DOMAIN_MODEL_VERSION)

        self._deployment = None

    @staticmethod
    def is_model_service(k8s_service):
        """
        Check that k8s service is legion model service

        :param k8s_service: K8S service
        :type k8s_service: V1Service
        :return: bool -- is legion model service
        """
        return k8s_service.metadata.labels and all(header in k8s_service.metadata.labels
                                                   for header in [DOMAIN_MODEL_ID, DOMAIN_MODEL_VERSION])

    @property
    def id(self):
        """
        Get model id

        :return: str -- ID of model
        """
        return self._model_id

    @property
    def version(self):
        """
        Get model version

        :return: str -- version of model
        """
        return self._model_version

    @property
    def id_and_version(self):
        """
        Get ModelIdVersion structure for current model

        :return: :py:class:`legion.k8s.ModelIdVersion`
        """
        return ModelIdVersion(self.id, self.version)

    @property
    def deployment(self):
        """
        Get model deployment

        :return: :py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`
        """
        self._load_data()
        return self._deployment

    def _load_data(self):
        """
        Load all required data (lazy loading)

        :return: None
        """
        if self._data_loaded:
            return

        client = legion.k8s.utils.build_client()

        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
        all_deployments = extension_api.list_namespaced_deployment(self._k8s_service.metadata.namespace)
        model_deployments = [deployment for deployment in all_deployments.items
                             if deployment.metadata.labels.get(DOMAIN_MODEL_ID) == self.id
                             and deployment.metadata.labels.get(DOMAIN_MODEL_VERSION) == self.version]

        self._deployment = model_deployments[0] if model_deployments else None

        super()._load_data()

    @property
    def scale(self):
        """
        Ger current scale

        :return: int -- current model scale
        """
        self._load_data()
        return self.deployment.status.available_replicas if self.deployment.status.available_replicas else 0

    @scale.setter
    def scale(self, new_scale):
        """
        Scale existed model deployment

        :param new_scale: new scale
        :type new_scale: int
        :return: None
        """
        self._load_data()
        client = legion.k8s.utils.build_client()

        extension_api = kubernetes.client.ExtensionsV1beta1Api(client)

        old_scale = self._deployment.spec.replicas
        self._deployment.spec.replicas = new_scale

        LOGGER.info('Scaling service {} in namespace {} from {} to {} replicas'
                    .format(self._deployment.metadata.name, self._deployment.metadata.namespace, old_scale, new_scale))

        extension_api.patch_namespaced_deployment(self._deployment.metadata.name,
                                                  self._deployment.metadata.namespace,
                                                  self._deployment)

        self.reload_cache()

    def delete(self, grace_period_seconds=0):
        """
        Remove model from cluster

        :param grace_period_seconds: grace period in seconds
        :type grace_period_seconds: int
        :return: None
        """
        client = legion.k8s.utils.build_client()

        api_instance = kubernetes.client.AppsV1beta1Api(client)
        core_v1api = kubernetes.client.CoreV1Api(client)

        body = kubernetes.client.V1DeleteOptions(propagation_policy='Background',
                                                 grace_period_seconds=grace_period_seconds)

        LOGGER.info('Deleting service {} in namespace {}'.format(self.k8s_service.metadata.name, self.namespace))
        core_v1api.delete_namespaced_service(name=self.k8s_service.metadata.name,
                                             namespace=self.namespace)

        LOGGER.info('Deleting deployment {} in namespace {} with grace period {}s'
                    .format(self.deployment.metadata.name, self.namespace, grace_period_seconds))
        api_instance.delete_namespaced_deployment(name=self.deployment.metadata.name,
                                                  namespace=self.namespace, body=body,
                                                  grace_period_seconds=grace_period_seconds,
                                                  propagation_policy='Background')

    @property
    def desired_scale(self):
        """
        Get desired model scale

        :return: int -- desired model scale
        """
        self._load_data()
        return self.deployment.status.replicas if self.deployment.status.replicas else 0

    @property
    def status(self):
        """
        Get model status

        :return: str -- model status
        """
        self._load_data()
        status = STATUS_OK

        if self.scale == 0:
            status = STATUS_FAIL
        elif self.desired_scale > self.scale > 0:
            status = STATUS_WARN

        return status

    @property
    def image(self):
        """
        Get model image

        :return: str -- model image
        """
        self._load_data()
        return self.deployment.spec.template.spec.containers[0].image

    @property
    def metrics_name(self):
        """
        Get model metrics name

        :return: str -- metrics name
        """
        return '{}.{}'.format(legion.k8s.utils.normalize_name(self.id, dns_1035=True),
                              legion.k8s.utils.normalize_name(self.version, dns_1035=True))

    def __str__(self):
        """
        Get string representation

        :return: str
        """
        return 'ModelService for model {} version {}'.format(self.id, self.version)

    __repr__ = name = __str__


class ModelServiceEndpoint:
    """
    Structure for describing model service with their endpoint (for specific version or default)
    """

    def __init__(self, model_service, default=False):
        """
        Build structure for model service (may used with default flag)

        :param model_service: model service
        :type model_service: :py:class:`legion.k8s.services.ModelService`
        :param default: (Optional) build default (not version locked url)
        :type default: bool
        """
        self._model_service = model_service
        self._default = default

    @property
    def model_service(self):
        """
        Get linked model service

        :return: :py:class:`legion.k8s.services.ModelService` -- model service
        """
        return self._model_service

    @property
    def url(self):
        """
        Get model url

        :return: str -- model url (relative to model API root)
        """
        if self._default:
            return '{}'.format(self.model_service.id)
        else:
            return '{}/{}'.format(self.model_service.id, self.model_service.version)

    def build_default(self):
        """
        Get ModelServiceEndpoint with enabled default flag for current model service

        :return: :py:class:`legion.k8s.services.ModelServiceEndpoint` -- new structure
        """
        return ModelServiceEndpoint(self._model_service, default=True)

    def __str__(self):
        """
        Get string representation

        :return: str
        """
        return 'ModelServiceEndpoint for MS {} default {}, url {}'.format(self.model_service, self._default, self.url)

    __repr__ = __str__

    def __hash__(self):
        """
        Get hash of current endpoint

        :return: int -- hash of current object
        """
        return hash(self.url)

    def __eq__(self, other):
        """
        Check equality

        :return: bool -- is items equal
        """
        return self.url == other.url
