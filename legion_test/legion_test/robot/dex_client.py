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
AUTHENTICATION_HOSTNAME = 'https://dex.{}/'
PARAM_NAME_LOGIN = 'login'
PARAM_NAME_PASSWORD = 'password'
SESSION_ID_COOKIE_NAMES = ('_oauth2_proxy', 'JSESSION')
AUTH_ENDPOINT_URLS = ('https://dashboard.{}/', 'https://jenkins.{}/securityRealm/commenceLogin',)
JENKINS_PROFILE_URL = 'https://jenkins.{}/user/{}/configure'
JENKINS_API_TOKEN_REGEX = re.compile('<input [^>]*id="apiToken"[^>]*value="([^"]+)"[^>]*>')

_session_cookies = {}
_jenkins_credentials = None

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
    global _session_cookies, _jenkins_credentials
    session = Session()
    for auth_endpoint_url in AUTH_ENDPOINT_URLS:
        response = session.get(auth_endpoint_url.format(cluster_host))
        if response.status_code != 200:
            raise IOError('Authentication endpoint is unavailable, got {} http code'
                          .format(response.status_code))
        if response.url.startswith(AUTHENTICATION_HOSTNAME.format(cluster_host)): # if auth form is opened
            match = re.search(REQUEST_ID_REGEXP, response.text)
            if match:
                request_id = match.group(1)
            else:
                raise ValueError('Request ID was not found on page')

            response = session.post(AUTHENTICATION_PATH.format(cluster_host, request_id),
                                {PARAM_NAME_LOGIN: login, PARAM_NAME_PASSWORD: password})
            if response.status_code != 200:
                raise IOError('Unable to authorise, got {} http code'
                              .format(response.status_code))

        for cookie_name in session.cookies.keys():
            if cookie_name.startswith(SESSION_ID_COOKIE_NAMES):
                _session_cookies[cookie_name]= session.cookies.get(cookie_name)
        if len(_session_cookies) == 0:
            raise ValueError('Cant find any session ID in Cookies')

    response = session.get(JENKINS_PROFILE_URL.format(cluster_host, login))
    if response.status_code == 200:

        regex_output = JENKINS_API_TOKEN_REGEX.search(response.text)
        if regex_output:
            _jenkins_credentials = (login, regex_output.group(1))


def get_session_cookies():
    """Get session cookies that can be used inside Request.
    :return: cookies dict or empty dict if Session ID wasn't found
    """
    return _session_cookies

def get_jenkins_credentials():
    """Get credentials (username and API Token) for Jenkins API,
    if they are found.
    :return: (username, password) or None"""
    return _jenkins_credentials
