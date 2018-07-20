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
legion k8s properties class
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
import legion.utils

LOGGER = logging.getLogger(__name__)


class K8SPropertyStorage:
    def __init__(self, k8s_namespace, storage_name, is_secret):
        self._k8s_namespace = k8s_namespace
        self._storage_name = storage_name
        self._is_secret = is_secret
        self._state = None

    def __setitem__(self, key, value):
        pass

    def __getitem__(self, item):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def watch(self):
        yield {}

    def watch_key(self, key):
        yield None
