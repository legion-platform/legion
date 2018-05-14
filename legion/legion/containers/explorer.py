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
import legion.containers.k8s
from legion.external.edi import EdiClient
import asyncio, os

MODEL_ID_SERVICE_LABEL = legion.containers.headers.DOMAIN_MODEL_ID
LEGION_COMPONENT_LABELS = 'legion/component', 'legion.component'


class Enclave:
    """
    Contains overall information about enclave, its services and models
    """
    def __init__(self, name, models, edi_service, edge_service, grafana_service, graphite_service):
        self._name = name
        self._models = models or {}
        self._edi_service = edi_service
        self._edge_service = edge_service
        self._grafana_service = grafana_service
        self._graphite_service = graphite_service

    @property
    def name(self):
        """
        Returns enclave name, usually it equals to K8s namespace name
        :return: Enclave name
        """
        return self._name

    @property
    def edi_service(self):
        return self._edi_service

    @property
    def edge_service(self):
        return self._edge_service

    @property
    def grafana_service(self):
        return self._grafana_service

    @property
    def graphite_service(self):
        return self._graphite_service

    @property
    def models(self):
        return self._models

    @property
    def edi_client(self):
        if self._edi_service is not None:
            return legion.external.edi.EdiClient('http://%s.%s' % (self.edi_service, self._name))


def find_enclaves(namespace=''):
    """
    Gets a list of enclaves
    :return: List of enclaves names
    :rtype list[Enclave]
    """
    enclaves_services = {}
    enclaves_models_services = {}

    list_edi_services = legion.containers.k8s.find_all_services(namespace=namespace)
    for service in list_edi_services:
        namespace = service.metadata.namespace
        component_name = next((service.metadata.labels.get(legion_label) for legion_label in LEGION_COMPONENT_LABELS
                          if legion_label in service.metadata.labels), None)
        if component_name is not None: # found a legion component
            if not namespace in enclaves_services:
                enclaves_services[namespace] = {}
                enclaves_services[namespace][component_name] = service.metadata.name
        elif MODEL_ID_SERVICE_LABEL in service.metadata.labels: # found a model service
            if not namespace in enclaves_models_services:
                enclaves_models_services[namespace] = {}
            model_id = service.metadata.labels.get(MODEL_ID_SERVICE_LABEL)
            enclaves_models_services[namespace][model_id] = service

    enclaves = []
    for enclave_name, services in enclaves_services.items():
        if 'edi' not in services: # if namspace doesn't have Edi server, it's not an enclave
            enclaves += [Enclave(enclave_name, enclaves_models_services.get(enclave_name, None),
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


async def render(template_system, *args, **kwargs):
    """
    Updates template context and renders it.

    :param template_system: Object, that contains 'render' callback function
    :param args: extra arguments
    :param kwargs: extra kwargs
    :return:
    """
    namespace = os.environ.get('NAMESPACE', '')
    if not namespace:
        raise ValueError("NAMESPACE wasn't found in env var.")
    while True:
        for event_type, enclave in watch_enclaves_update(namespace, watch_for_models=True):
            template_system.render(enclave=enclave)