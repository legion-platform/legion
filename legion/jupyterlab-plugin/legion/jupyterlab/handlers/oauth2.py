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
Oauth2 callback handler
"""
from legion.jupyterlab.handlers.base import build_redirect_url, build_oauth_url
from legion.jupyterlab.handlers.cloud import BaseCloudLegionHandler
from legion.jupyterlab.handlers.helper import decorate_handler_for_exception, LEGION_OAUTH_STATE_COOKIE_NAME, \
    LEGION_OAUTH_TOKEN_COOKIE_NAME
from legion.sdk.clients.oauth_handler import get_oauth_token_issuer_url, get_id_token

OAUTH_STATE_ARGUMENT = 'state'
JUPYTERLAB_MAIN_PAGE = '/lab?'


# pylint: disable=W0223
class OAuth2Callback(BaseCloudLegionHandler):
    """
    Oauth2 callback handler
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Retrieve and save the id token

        :return: None
        """
        # pylint: disable=E1120
        if self.get_argument(OAUTH_STATE_ARGUMENT) != self.get_cookie(LEGION_OAUTH_STATE_COOKIE_NAME):
            raise ValueError('State parameters from application and authorization server are different.')

        code = self.get_argument('code', strip=True)
        target_url, _ = build_oauth_url()

        issue_token_url = get_oauth_token_issuer_url(target_url)
        if not issue_token_url:
            raise Exception(f'Can not get URL for issuing long-life token from {target_url}')

        login_result = get_id_token(code, issue_token_url, build_redirect_url())
        if not login_result:
            raise Exception(f'Failed to get long-life token from {issue_token_url}')

        self.set_cookie(LEGION_OAUTH_TOKEN_COOKIE_NAME, login_result.id_token)

        self.redirect(JUPYTERLAB_MAIN_PAGE)


# pylint: disable=W0223
class OAuth2Info(BaseCloudLegionHandler):
    """
    Oauth2 info handler
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Builds and returns oauth url of authorization server

        :return: None
        """
        oauth_url, state = build_oauth_url()
        self.set_cookie(LEGION_OAUTH_STATE_COOKIE_NAME, state)

        self.finish(oauth_url)
