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
legion k8s definitions functions
"""
import typing

LEGION_SYSTEM_LABEL = 'legion.system'
LEGION_SYSTEM_VALUE = 'yes'
LEGION_COMPONENT_LABEL = 'legion.component'
LEGION_COMPONENT_NAME_MODEL = 'model'
LEGION_COMPONENT_NAME_EDI = 'edi'
LEGION_COMPONENT_NAME_API = 'edge'
LEGION_COMPONENT_NAME_GRAFANA = 'grafana'
LEGION_COMPONENT_NAME_GRAPHITE = 'graphite'

LEGION_API_SERVICE_PORT = 'api'

ENCLAVE_NAMESPACE_LABEL = 'enclave'

INGRESS_DASHBOARD_NAME = 'kubernetes-dashboard'
INGRESS_GRAFANA_NAME = 'legion-core-grafana'


EVENT_ADDED = 'ADDED'
EVENT_MODIFIED = 'MODIFIED'
EVENT_DELETED = 'DELETED'

LOAD_DATA_ITERATIONS = 5
LOAD_DATA_TIMEOUT = 2

ModelContainerMetaInformation = typing.NamedTuple('ModelContainerMetaInformation', [
    ('k8s_name', str),
    ('model_id', str),
    ('model_version', str),
    ('kubernetes_labels', typing.Dict[str, str]),
    ('kubernetes_annotations', typing.Dict[str, str]),
])
