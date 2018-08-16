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
legion k8s module
"""
from legion.k8s.enclave import Enclave, find_enclaves
from legion.k8s.services import Service, ModelService
from legion.k8s.definitions import ModelIdVersion, ModelDeploymentDescription
from legion.k8s.definitions import STATUS_OK, STATUS_FAIL, STATUS_WARN
from legion.k8s.definitions import EVENT_ADDED, EVENT_MODIFIED, EVENT_DELETED
from legion.k8s.utils import build_client, get_current_namespace, load_config, load_secrets
from legion.k8s.utils import CONNECTION_CONTEXT
from legion.k8s.watch import ResourceWatch
from legion.k8s.properties import K8SPropertyStorage, K8SConfigMapStorage, K8SSecretStorage
