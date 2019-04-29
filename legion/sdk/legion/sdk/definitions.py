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

LEGION_SYSTEM_LABEL = 'app.kubernetes.io/name'
LEGION_SYSTEM_VALUE = 'legion'
LEGION_COMPONENT_LABEL = 'component'
LEGION_COMPONENT_NAME_MODEL = 'legion-model'
LEGION_COMPONENT_NAME_EDI = 'legion-edi'
LEGION_COMPONENT_NAME_API = 'legion-edge'

LEGION_API_SERVICE_PORT = 'api'

ENCLAVE_NAMESPACE_LABEL = 'enclave'

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

EDI_VERSION = 'v1'
EDI_ROOT = '/'
EDI_API_ROOT = '/api/'
EDI_DEPLOY = '/api/{version}/deploy'
EDI_UNDEPLOY = '/api/{version}/undeploy'
EDI_SCALE = '/api/{version}/scale'
EDI_INSPECT = '/api/{version}/inspect'

VCS_URL = '/api/{version}/vcs'
MODEL_TRAINING_URL = '/api/{version}/model/training'
MODEL_DEPLOYMENT_URL = '/api/{version}/model/deployment'
MODEL_TOKEN_TOKEN_URL = '/api/{version}/model/token'

DOCKER_BUILD_URL = '/api/1.0/build'

KUBERNETES_SERVICE_ACCOUNT_NAMESPACE_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
