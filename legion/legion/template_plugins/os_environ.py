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
Environment variables provider for Legion Template
"""
import logging
import os

LOGGER = logging.getLogger(__name__)


def environment_variables_provider(template_system):
    """
    Update template context with environment variables values

    :param template_system: Object, that contains 'render' callback function
    :return: None
    """
    LOGGER.info('Render template with environ variables')
    template_system.render(environ=os.environ)
