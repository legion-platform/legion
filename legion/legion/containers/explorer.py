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
legion explorer functions, returns legion models, services details
"""
from unicodedata import name

import legion.containers.k8s
from legion.external.edi import EdiClient
import asyncio
import os

MODEL_ID_SERVICE_LABEL = legion.containers.headers.DOMAIN_MODEL_ID
LEGION_COMPONENT_LABELS = 'legion/component', 'legion.component'
INGRESS_COMPONENT_LABEL = 'component'
NON_ENCLAVE_NAMESPACES = 'default', 'kube-system'

INGRESS_DASHBOARD_NAME = 'kubernetes-dashboard'
INGRESS_GRAFANA_NAME = 'legion-core-grafana'


class Enclave:
    """
    Contains overall information about enclave, its services and models
    """

    def __init__(self, name, models, grafana_hostname, edi_service, edge_service,
                 grafana_service, graphite_service):
        """
        Create an Enclave instance
        :param name: enclave name
        :param models: dict of models
        :param grafana_hostname: public grafana hostname
        :param edi_service: EDI V1Service object
        :param edge_service: Edge V1Service object
        :param grafana_service: Grafana V1Service object
        :param graphite_service: Graphite V1Service object
        :param
        """
        self._name = name
        self._models = models or {}
        self._grafana_hostname = grafana_hostname
        self._edi_service = edi_service
        self._edge_service = edge_service
        self._grafana_service = grafana_service
        self._graphite_service = graphite_service

    @property
    def name(self):
        """
        Return enclave name, usually it equals to K8s namespace name
        :return: Enclave name
        """
        return self._name

    @property
    def edi_service(self):
        """
        Return EDI service object.
        :rtype V1Service
        :return: EDI service object
        """
        return self._edi_service

    @property
    def edge_service(self):
        """
        Return Edge service object.
        :rtype V1Service
        :return: Edge service object
        """
        return self._edge_service

    @property
    def grafana_service(self):
        """
        Return Grafana service object.
        :rtype V1Service
        :return: Grafana service object
        """
        return self._grafana_service

    @property
    def grafana_hostname(self):
        """
        Return public hostname of Grafana service.
        :rtype str
        :return: public hostname of Grafana service
        """
        return self._grafana_hostname

    @property
    def graphite_service(self):
        """
        Return Graphite service object.
        :rtype V1Service
        :return: Graphite service object
        """
        return self._graphite_service

    @property
    def models(self):
        """
        Return a dict of Models services.
        :rtype dict(str, V1Service)
        :return: dict of deployed Models (Model ID, Model service)
        """
        return self._models

    @property
    def edi_client(self):
        """
        Return an EDI Client object for Edi server in the Enclave
        :rtype EdiClient
        :return: an EDI Client object
        """
        if self._edi_service is not None:
            return legion.external.edi.EdiClient('http://%s.%s' % (self.edi_service, self._name))


def find_public_hosts():
    """
    Get a dictionary of public host names.
    :return: a dictionary of public host names per service name
    :rtype: dict(str, str)
    """
    ingresses = {}
    # load data for all ingresses: enclaves and system
    list_ingresses = legion.containers.k8s.find_all_ingresses()
    for ingress in list_ingresses:
        ingress_namespace = ingress.metadata.namespace
        if ingress_namespace in NON_ENCLAVE_NAMESPACES:
            # get 'public' hostnames
            if ingress.spec.rules and len(ingress.spec.rules) > 0:
                ingresses[ingress.metadata.name] = ingress.spec.rules[0].host
    return ingresses


def get_public_dashboard_hostname():
    """
    Get public hostname of a Kubernetes dashboard
    :return: hostname of a Kubernetes dashboard
    :rtype: str
    """
    return find_public_hosts().get(INGRESS_DASHBOARD_NAME, None)


def get_public_grafana_hostname():
    """
    Get public hostname of a Grafana Web UI
    :return: hostname of a Grafana Web UI
    :rtype: str
    """
    return find_public_hosts().get(INGRESS_DASHBOARD_NAME, None)


def find_enclaves(namespace=''):
    """
    Get a list of enclaves
    :return: List of enclaves names
    :rtype list[Enclave]
    """
    enclaves_services = {}
    enclaves_models_services = {}
    enclaves_ingresses = {}

    list_services = legion.containers.k8s.find_all_services(namespace=namespace)
    for service in list_services:
        service_namespace = service.metadata.namespace
        component_name = next((service.metadata.labels.get(legion_label) for legion_label in LEGION_COMPONENT_LABELS
                               if legion_label in service.metadata.labels), None)
        if component_name is not None:  # found a legion component
            if service_namespace not in enclaves_services:
                enclaves_services[service_namespace] = {}
                enclaves_services[service_namespace][component_name] = service.metadata.name
        elif MODEL_ID_SERVICE_LABEL in service.metadata.labels:  # found a model service
            if service_namespace not in enclaves_models_services:
                enclaves_models_services[service_namespace] = {}
            model_id = service.metadata.labels.get(MODEL_ID_SERVICE_LABEL)
            enclaves_models_services[service_namespace][model_id] = service

    # load data for all ingresses: enclaves and system
    list_ingresses = legion.containers.k8s.find_all_ingresses(namespace=namespace)
    for ingress in list_ingresses:
        ingress_namespace = ingress.metadata.namespace
        if INGRESS_COMPONENT_LABEL in ingress.metadata.labels:
            if ingress_namespace not in enclaves_ingresses:
                enclaves_ingresses[ingress_namespace] = {}
            # get a component name and it's 'public' hostname
            component_name = ingress.metadata.labels[INGRESS_COMPONENT_LABEL]
            if ingress_namespace in component_name:
                component_name = component_name.split(ingress_namespace+'-')[-1]
            if ingress.spec.rules and len(ingress.spec.rules) > 0:
                enclaves_ingresses[ingress_namespace][component_name] = ingress.spec.rules[0].host

    enclaves = []
    for enclave_name, services in enclaves_services.items():
        if 'edi' in services:  # if namespace doesn't have Edi server, it's not an enclave
            enclaves += [Enclave(enclave_name, enclaves_models_services.get(enclave_name, None),
                                 enclaves_ingresses.get(enclave_name, {}).get('grafana', None),
                                 services.get('edi', None), services.get('edge', None),
                                 services.get('grafana', None), services.get('graphite', None))]

    return enclaves


def watch_enclaves_update(enclave_name='', watch_for_models=False, watch_for_enclaves=False):
    """
    Watch for enclave updates
    :param enclave_name: Enclave name to watch for
    :param watch_for_models: Indicates, if need to watch for models (ADDED, DELETED, MODIFIED)
    :param watch_for_enclaves: Indicates, if need to watch for enclaves (ADDED, DELETED)
    :return: (event type [ADDED, DELETED, MODIFIED], enclave object)
    :rtype (str, Enclave)
    """
    enclaves = dict((enclave.name, enclave) for enclave in find_enclaves(enclave_name))
    for event_type, service in legion.containers.k8s.watch_all_services(enclave_name):
        namespace = service.metadata.namespace
        component_name = next((service.metadata.labels.get(legion_label) for legion_label in LEGION_COMPONENT_LABELS
                               if legion_label in service.metadata.labels), None)
        if component_name == 'edi' and watch_for_enclaves:
            if event_type == 'DELETED' and namespace in enclaves:
                yield (event_type, enclaves.pop(namespace))
            elif event_type == 'ADDED' and namespace not in enclaves:
                enclaves[namespace] = find_enclaves(namespace)
                yield (event_type, enclaves[namespace])
        elif MODEL_ID_SERVICE_LABEL in service.metadata.labels and watch_for_models:
            model_id = service.metadata.labels.get(MODEL_ID_SERVICE_LABEL)
            if event_type == 'ADDED' and model_id not in enclaves[namespace].models:
                enclaves[namespace].models[model_id] = service
                yield ('MODIFIED', enclaves[namespace])
            elif event_type == 'MODIFIED':
                enclaves[namespace].models[model_id] = service
                yield ('MODIFIED', enclaves[namespace])
            elif event_type == 'DELETED':
                enclaves[namespace].models.pop(model_id)
                yield ('MODIFIED', enclaves[namespace])


async def render_on_enclave_change(template_system):
    """
    Update template context and renders it.

    :param template_system: Object, that contains 'render' callback function
    :param args: extra arguments
    :param kwargs: extra kwargs
    :return:
    """
    namespace = os.environ.get('NAMESPACE', '')
    if not namespace:
        raise ValueError("NAMESPACE wasn't found in env var.")
    enclaves = find_enclaves(namespace)
    if enclaves and len(enclaves) == 1:
        template_system.render(enclave=enclaves[0])
    while True:
        for event_type, enclave in watch_enclaves_update(namespace, watch_for_models=True):
            template_system.render(enclave=enclave)
