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
Enclave models Notifier module for Legion Template
"""
import logging

from legion.k8s import Enclave
from legion.k8s.utils import get_current_namespace

LOGGER = logging.getLogger(__name__)


async def enclave_models_monitor(template_system):
    """
    Update template with current model state

    :param template_system: Object, that contains 'render' callback function
    :return: None
    """
    namespace = get_current_namespace()
    LOGGER.info('Starting models monitor in namespace {}'.format(namespace))

    enclave = Enclave(namespace)
    LOGGER.info('Loaded enclave {}'.format(enclave))

    for new_state in enclave.watch_model_service_endpoints_state():
        LOGGER.info('Got updated model state')
        template_system.render(models=new_state)
