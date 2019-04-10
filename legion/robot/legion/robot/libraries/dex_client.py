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
import logging
import re
import time

import requests
from requests.sessions import Session

REQUEST_ID_REGEXP = re.compile(r'/auth/local\?req=([^"]+)')
AUTHENTICATION_PATH = 'https://dex.{}/auth/local?req={}'
AUTHENTICATION_HOSTNAME = 'https://dex.{}/'
PARAM_NAME_LOGIN = 'login'
PARAM_NAME_PASSWORD = 'password'
SESSION_ID_COOKIE_NAMES = ('_oauth2_proxy', 'JSESSION')
AUTH_ENDPOINT_URLS = ('https://dashboard.{}/',)
AUTH_RETRY_TIMEOUT = 10
NUMBER_AUTH_RETRIES = 10

_session_cookies = {}

LOGGER = logging.getLogger(__name__)


def init_session_id_from_data(data: dict):
    """
    Initialize Session ID value from serialized data

    :param data: persisted login data
    :type data: dict[str, str]
    """
    global _session_cookies
    if not _session_cookies:
        cookies = data['cookies'].split(';')
        for cookie in cookies:
            cookie = cookie.replace('=', ':', 1)
            _session_cookies[cookie.split(':')[0]] = cookie.split(':')[1]


def auth_on_dex(service_url: str, cluster_host: str, login: str, password: str, session=None):
    """
    Log in on dex

    :param service_url: template of url
    :type service_url: str
    :param cluster_host: base host of a cluster
    :type cluster_host: str
    :param login: dex static user
    :type login: str
    :param password: password of a dex static user
    :type password: str
    :param session: request Session
    :type session: Optional[Session]
    :return: final response - Response
    """
    if not session:
        session = Session()

    resp = session.get(service_url)
    if resp.status_code != 200:
        requests.HTTPError('Authentication endpoint is unavailable, got {} http code'
                           .format(resp.status_code))

    if resp.url.startswith(AUTHENTICATION_HOSTNAME.format(cluster_host)):  # if auth form is opened
        match = re.search(REQUEST_ID_REGEXP, resp.text)
        if match:
            request_id = match.group(1)
        else:
            raise ValueError('Request ID was not found on page')

        url = AUTHENTICATION_PATH.format(cluster_host, request_id)
        data = {PARAM_NAME_LOGIN: login, PARAM_NAME_PASSWORD: password}
        resp = session.post(url, data)
        if resp.status_code != 200:
            raise requests.HTTPError('Unable to authorise, got {} http code from {} '  # pylint: disable=E1305
                                     'for the query to {} with data, resp {}'
                                     .format(resp.status_code, service_url, url, data, resp.text))

    return resp


def init_session_id(login: str, password: str, cluster_host: str) -> None:
    """
    Initialize Session ID value from a Cookie after authentication.

    :param login: Login of a Static Dex user
    :type login: str
    :param password: Password of a Static Dex user
    :type password: str
    :param cluster_host: Base Host of a cluster
    :type cluster_host: str
    :return: None
    """
    global _session_cookies
    session = Session()
    for auth_endpoint_url in AUTH_ENDPOINT_URLS:
        for _ in range(NUMBER_AUTH_RETRIES):
            try:
                auth_on_dex(auth_endpoint_url.format(cluster_host), cluster_host, login, password, session)

                break
            except requests.HTTPError as e:
                LOGGER.error('Failed with exception: %s. Waiting %s seconds before next retry analysis',
                             str(e), AUTH_RETRY_TIMEOUT)

                time.sleep(AUTH_RETRY_TIMEOUT)
        else:
            raise Exception(f"Number of auth retries were exceed")

        for cookie_name in session.cookies.keys():
            if cookie_name.startswith(SESSION_ID_COOKIE_NAMES):
                _session_cookies[cookie_name] = session.cookies.get(cookie_name)
        if not _session_cookies:
            raise ValueError('Cant find any session ID in Cookies')


def get_session_cookies():
    """
    Get session cookies that can be used inside Request.

    :return: cookies dict or empty dict if Session ID wasn't found
    """
    return _session_cookies


def get_token():
    """
    Get token from session cookies that can be used inside Request.

    :return: str -- jwt
    """
    return _session_cookies['_oauth2_proxy']
