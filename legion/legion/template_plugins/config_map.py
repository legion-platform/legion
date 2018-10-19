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
Config map Notifier module for Legion Template
"""
import logging

from legion.k8s import K8SConfigMapStorage
from legion.k8s.utils import get_current_namespace

LOGGER = logging.getLogger(__name__)


async def invalid_token_monitor(template_system):
    """
    Update template with current model state

    :param template_system: Object, that contains 'render' callback function
    :return: None
    """
    namespace = get_current_namespace()
    LOGGER.info('Starting models monitor in namespace {}'.format(namespace))

    config_map = K8SConfigMapStorage(storage_name="invalid_tokens",
                                     k8s_namespace=namespace)


    for _, new_state in config_map.watch():
        LOGGER.info('Got updated model state')
        template_system.render(tokens=new_state['invalid_tokens'])
