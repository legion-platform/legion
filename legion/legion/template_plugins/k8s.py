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
Enclave configmaps update notifier module for Legion Template
"""
import logging

from legion.k8s.utils import get_current_namespace
from legion.k8s import K8SConfigMapStorage

LOGGER = logging.getLogger(__name__)


def enclave_configmap_monitor(template_system, var_name="var"):
    """
    Update template with current model state

    :param template_system: Object, that contains 'render' callback function
    :return: None
    """
    namespace = get_current_namespace()
    LOGGER.info('Starting configmap monitor in namespace {}'.format(namespace))

    config_map = K8SConfigMapStorage.retrive(
        storage_name="legion-{}-invalid-tokens".format(namespace),
        k8s_namespace=namespace)
    LOGGER.info("initial value is {}".format(config_map.data))

    for event, new_state in config_map.watch():
        LOGGER.info('Got updated configmap state')
        LOGGER.info("New state is {}".format(new_state))
        template_system.render(**{var_name: new_state})
