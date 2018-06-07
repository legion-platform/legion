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
from legion.k8s import Enclave
from legion.k8s.utils import get_current_namespace


async def enclave_models_monitor(template_system):
    """
    Update template with current model state

    :param template_system: Object, that contains 'render' callback function
    :return: None
    """
    enclave = Enclave(get_current_namespace())

    for new_state in enclave.watch_model_service_endpoints_state():
        template_system.render(models=new_state)
