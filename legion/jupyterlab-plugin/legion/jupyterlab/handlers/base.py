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
Declaration of base back-end handler
"""
import json
import random
import string
from typing import Tuple

from urllib.parse import urlencode
from notebook.base.handlers import APIHandler

from legion.jupyterlab.handlers.helper import LEGION_X_JWT_TOKEN
from legion.sdk import config

OAUTH_STATE_LENGTH = 10


def build_redirect_url() -> str:
    """
    Build Jupyterlab redirect URL
    :return: URL
    """
    return f'{config.JUPYTER_REDIRECT_URL}/legion/api/oauth2/callback'


def build_oauth_url() -> Tuple[str, str]:
    """
    Build full oauth URL
    :return: URL and state
    """
    state = ''.join(random.choice(string.ascii_letters) for _ in range(OAUTH_STATE_LENGTH))

    parameters = {
        'client_id': config.LEGIONCTL_OAUTH_CLIENT_ID,
        'response_type': 'code',
        'state': state,
        'redirect_uri': build_redirect_url(),
        'scope': config.LEGIONCTL_OAUTH_SCOPE
    }

    return f'{config.LEGIONCTL_OAUTH_AUTH_URL}?{urlencode(parameters)}', state


# pylint: disable=W0223
class BaseLegionHandler(APIHandler):
    """
    Base handler for Legion plugin back-end
    """

    def __init__(self, *args, **kwargs):
        """
        Construct base handler w/o state & logger

        :param args: additional args (is passed to parent)
        :param kwargs: additional k-v args (is passed to parent)
        """
        super().__init__(*args, **kwargs)
        self.state = None
        self.logger = None
        self.templates = None

    def initialize(self, state, logger, templates, **kwargs):
        """
        Initialize base handler

        :param state: state of plugin back-end
        :param logger: logger to log data to
        :param kwargs: additional arguments
        :return: None
        """
        self.state = state
        self.logger = logger
        self.templates = templates
        self.logger.debug('%s initialized', self.__class__.__name__)

    def finish_with_json(self, data=None):
        """
        Finish request (response to client) with JSON

        :param data: JSON-serializable object
        :type data: any
        :return: None
        """
        self.finish(json.dumps(data))

    def get_token_from_header(self) -> str:
        """
        Returns a JWT from the oauth proxy header
        :return: JWT
        """
        return self.request.headers.get(LEGION_X_JWT_TOKEN, '')
