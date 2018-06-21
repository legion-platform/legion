#
#    Copyright 2017 EPAM Systems
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
"""Dex authentication client."""
from requests.sessions import Session
import re

REQUEST_ID_REGEXP = re.compile('/auth/local\?req=([^"]+)')
AUTHENTICATION_PATH = 'https://dex.{}/auth/local?req={}'
PARAM_NAME_LOGIN = 'login'
PARAM_NAME_PASSWORD = 'password'
SESSION_ID_COOKIE_NAME = '_oauth2_proxy'
AUTH_ENDPOINT_URL = 'https://auth.{}'

_session_id = None


def init_session_id(login: str, password: str, cluster_host: str) -> None:
    """Initialize Session ID value from a Cookie after authentication.

    :param login: Login of a Static Dex user
    :type login: str
    :param password: Password of a Static Dex user
    :type password: str
    :param cluster_host: Base Host of a cluster
    :type cluster_host: str
    :return: None
    """
    global _session_id
    session = Session()
    response = session.get(AUTH_ENDPOINT_URL.format(cluster_host))
    if response.status_code != 200:
        raise IOError('Authentication endpoint is unavailable, got {} http code'
                      .format(response.status_code))
    match = re.search(REQUEST_ID_REGEXP, response.text)
    if match:
        request_id = match.group(1)
    else:
        raise ValueError('Request ID was not found on page')

    session.post(AUTHENTICATION_PATH.format(cluster_host, request_id),
                            {PARAM_NAME_LOGIN: login, PARAM_NAME_PASSWORD: password})
    if SESSION_ID_COOKIE_NAME in session.cookies:
        _session_id = session.cookies.get(SESSION_ID_COOKIE_NAME)
    else:
        raise ValueError('Cant find session ID in Cookies')


def get_session_id() -> str:
    """Get stored Session ID value.

    :return: session ID value
    """
    if _session_id:
        return _session_id
    else:
        raise ValueError('Session ID is not inited')


def get_session_cookies() -> dict:
    """Get session cookies that can be used inside Request.
    :return: cookies dict
    """
    if _session_id:
        return {SESSION_ID_COOKIE_NAME: _session_id}
    else:
        # Dex is disabled or Session ID wasn't found
        return
