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
"""
Authentication client.
"""
import logging

import requests


_auth_jwt = None

LOGGER = logging.getLogger(__name__)


def init_token(login: str, password: str, auth_url: str, client_id: str, client_secret: str, scope: str) -> None:
    """
    Authorize test user and get access token.

    :param login: Login of a test user
    :type login: str
    :param password: Password of a test user
    :type password: str
    :param auth_url: Authorization endpoint
    :type auth_url: str
    :param auth_url: Authorization endpoint
    :type auth_url: str
    :param client_id: OAuth client id
    :type client_id: str
    :param client_secret: OAuth client secret
    :type client_secret: str
    :param scope: OAuth2 scope (space delimited scopes)
    :type scope: str
    :return: None
    """
    global _auth_jwt

    try:
        response = requests.post(
            auth_url,
            data={
                'grant_type': 'password',
                'client_id': client_id,
                'client_secret': client_secret,
                'username': login,
                'password': password,
                'scope': scope
            }
        )
        response_data = response.json()
        # Parse fields and return
        id_token = response_data.get('id_token')
        token_type = response_data.get('token_type')
        expires_in = response_data.get('expires_in')
        LOGGER.info('Received %s token with expiration in %d seconds', token_type, expires_in)
        _auth_jwt = id_token
    except requests.HTTPError as http_error:
        raise Exception(f'Can not authorize test user {login!r} on {auth_url!r}: {http_error}') from http_error

    return _auth_jwt


def get_authorization_headers():
    """
    Get authorization headers that can be used inside Request.

    :return: headers dict or empty dict if Session ID wasn't found
    """
    return {
        'Authorization': f'Bearer {_auth_jwt}'
    } if _auth_jwt else {}


def get_token():
    """
    Get JWT that can be used inside Request.

    :return: str or None -- jwt
    """
    return _auth_jwt
