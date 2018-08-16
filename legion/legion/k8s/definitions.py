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

ModelDeploymentDescription = typing.NamedTuple('ModelDeploymentDescription', [
    ('status', str),
    ('model', str),
    ('version', str),
    ('image', str),
    ('scale', int),
    ('ready_replicas', int),
    ('namespace', str),
    ('model_api_ok', bool),
    ('model_api_info', dict),
])
ModelIdVersion = typing.NamedTuple('ModelDeploymentDescription', [
    ('id', str),
    ('version', str),
])


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

STATUS_OK = 'ok'
STATUS_FAIL = 'fail'
STATUS_WARN = 'warning'

EVENT_ADDED = 'ADDED'
EVENT_MODIFIED = 'MODIFIED'
EVENT_DELETED = 'DELETED'
