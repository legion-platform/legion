#
#    Copyright 2019 EPAM Systems
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
Configuration handler
"""
import os

from legion.jupyterlab.handlers.base import BaseLegionHandler
from legion.jupyterlab.handlers.helper import decorate_handler_for_exception, \
    DEFAULT_EDI_ENDPOINT, LEGION_OAUTH_TOKEN_COOKIE_NAME
from legion.sdk import config
from legion.sdk.clients.templates import get_legion_template_names, get_legion_template_content


# pylint: disable=W0223


class ConfigurationProviderHandler(BaseLegionHandler):
    """
    Return configuration for current backend configuration
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all configuration for backend

        :return: None
        """
        self.finish_with_json({
            # Verify that all parameters are set
            'oauth2AuthorizationIsEnabled': bool(config.JUPYTER_REDIRECT_URL) and bool(
                config.LEGIONCTL_OAUTH_AUTH_URL),
            'idToken': self.get_cookie(LEGION_OAUTH_TOKEN_COOKIE_NAME, ''),
            'tokenProvided': bool(self.get_token_from_header()),
            'defaultEDIEndpoint': os.getenv(DEFAULT_EDI_ENDPOINT, ''),
            'legionResourceExamples': sorted(get_legion_template_names()),
        })


class TemplatesFilesHandler(BaseLegionHandler):

    def get(self, template_name):
        if template_name:
            self.finish(get_legion_template_content(template_name))
        else:
            self.set_status(404)
