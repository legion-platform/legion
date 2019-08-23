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
OAuth2 handler
"""
import base64
import socket
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from contextlib import closing
from urllib.parse import parse_qs, urlparse
import typing
import json

import requests

from legion.sdk import config
from legion.sdk.utils import render_template

LOGGER = logging.getLogger()


class OAuthLoginResult(typing.NamedTuple):
    """
    Result of oauth login process
    """

    access_token: str
    refresh_token: str
    id_token: str
    issuing_url: str
    user_email: str
    user_name: str


def find_free_port(bind_addr: str = '0.0.0.0') -> int:
    """
    Find next available port on local machine

    :return: int - port number
    """
    # pylint: disable=E1101
    # due to bug with closing return type
    LOGGER.debug('Trying to get free port')
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((bind_addr, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = sock.getsockname()[1]
        LOGGER.debug('Free port %d has been found', port)
        return port


def _try_to_extract_issuing_url_from_well_known_metadata(well_known_address: str) -> typing.Optional[str]:
    """
    Try to extract token issuing url from well-known location

    :param well_known_address: well-known URL
    :type well_known_address: str
    :return: str or None -- token issuing URL
    """
    try:
        LOGGER.debug('Trying to extract well-known information from address %r', well_known_address)
        response = requests.get(url=well_known_address)
        data = response.json()
    except requests.HTTPError as http_error:
        LOGGER.debug('Failed to extract well-known information from address %r - %s', well_known_address, http_error)
        return None
    except ValueError as value_error:
        LOGGER.debug('Failed to parse well-known information from address %r - %s', well_known_address, value_error)
        return None

    token_endpoint = data.get('token_endpoint')
    if not token_endpoint:
        LOGGER.debug('well-known information does not contain token_endpoint (%s)', well_known_address)
        return

    return token_endpoint


def get_oauth_token_issuer_url(redirect_url: str) -> typing.Optional[str]:
    """
    Get OAuth2 token issuing URL

    :param redirect_url: current redirection URL
    :type redirect_url: str
    :return: str or None -- token issuing URL
    """
    # 1st priority - check config variable LEGIONCTL_OAUTH_TOKEN_ISSUING_URL
    if config.LEGIONCTL_OAUTH_TOKEN_ISSUING_URL:
        return config.LEGIONCTL_OAUTH_TOKEN_ISSUING_URL

    # 2nd priority - try to remove URL parts of redirect URL and append /.well-known/openid-configuration
    # According to https://tools.ietf.org/pdf/rfc8414.pdf
    loc = urlparse(redirect_url)
    path_parts = loc.path.strip('/').split('/')

    for i in range(len(path_parts)):
        sub_path = '/'.join(path_parts[0:i])
        full_uri = f'{loc.scheme}://{loc.netloc}/{sub_path}/.well-known/openid-configuration'
        endpoint = _try_to_extract_issuing_url_from_well_known_metadata(full_uri)
        if endpoint:
            return endpoint
    return None


def _ask_token_endpoint(url: str, payload: typing.Any) -> typing.Optional[OAuthLoginResult]:
    """
    Query token endpoint to refresh / issue new token

    :param url: token endpoint
    :param payload: query payload
    :return: OAuthLoginResult or None -- login result or None
    """
    try:
        res = requests.post(url, data=payload)
        data = res.json()
    except requests.HTTPError as http_error:
        LOGGER.warning('Failed to get ID token on %r - %s', url, http_error)
        return None
    except ValueError as value_error:
        LOGGER.warning('Failed to get ID token on %r - %s', url, value_error)
        return None

    access_token, refresh_token, id_token = data.get('access_token'), data.get('refresh_token'), data.get('id_token')
    if not access_token or not refresh_token or not id_token:
        LOGGER.warning('Response does not contain access_token / refresh_token / id_token')
        return None

    _, body, _ = id_token.split('.')
    id_payload = json.loads(base64.b64decode(body + '===').decode('utf-8'))
    user_name = id_payload.get('name')
    user_email = id_payload.get('email')

    result = OAuthLoginResult(
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
        issuing_url=url,
        user_name=user_name,
        user_email=user_email
    )

    LOGGER.debug('Token information for %s / %s has been received', result.user_name, result.user_email)
    return result


def do_refresh_token(refresh_token: str, issue_token_url: str) -> typing.Optional[OAuthLoginResult]:
    """
    Refresh token using previously saved refresh_token

    :param refresh_token: refresh token
    :param issue_token_url: issue token URL
    :return: OAuthLoginResult or None -- refresh result or None
    """
    LOGGER.debug('Trying to refresh ID token using %s', issue_token_url)

    payload = {
        'grant_type': 'refresh_token',
        'client_id': config.LEGIONCTL_OAUTH_CLIENT_ID,
        'refresh_token': refresh_token
    }
    return _ask_token_endpoint(issue_token_url, payload)


def get_id_token(code: str, issue_token_url: str, redirect_uri: str) -> typing.Optional[OAuthLoginResult]:
    """
    Get ID token and validate received data

    :param code: code
    :param issue_token_url: issuing URL
    :param redirect_uri: redirect URL
    :return: OAuthLoginResult or None -- login result or None
    """
    LOGGER.debug('Trying to get ID token and validate using %s', issue_token_url)

    payload = {
        'grant_type': 'authorization_code',
        'client_id': config.LEGIONCTL_OAUTH_CLIENT_ID,
        'code': code,
        'redirect_uri': redirect_uri
    }
    return _ask_token_endpoint(issue_token_url, payload)


class OAuth2Handler(BaseHTTPRequestHandler):
    """
    Handler for simple loopback listening server that handles OAuth2 redirects to loopback host
    """

    def __init__(self, *args, on_token_received=None, state=None, target_url=None, redirect_url=None, **kwargs):
        """
        Initialize loopback server

        :param args: system args
        :param on_token_received: callback that should be called on final auth. stage (when all tokens are received)
        :param state: randomly generated token for OAuth2 pipeline
        :param target_url: captured redirect to IP's URL
        :param redirect_url:  redirect URL to continue authorization
        :param kwargs: system args
        """
        self.on_token_received = on_token_received
        self.state = state
        self.target_url = target_url
        self.redirect_url = redirect_url
        BaseHTTPRequestHandler.__init__(self, *args)

    def log_message(self, format: str, *args: typing.Tuple[typing.Any, ...]) -> None:
        """
        Log an arbitrary message.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        :param format: format
        :param args: arguments for format
        :return: None
        """
        LOGGER.debug('%s - %s', self.address_string(), format % args)

    def raise_error(self, message: str) -> None:
        """
        Raise error if it is a problem

        :param message: error description
        :type message: str
        :return: None
        """
        self.send_response(500)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    def do_GET(self) -> None:
        """
        Handle GET action

        :return: None
        """
        loc = urlparse(self.path)
        if loc.path == config.LEGIONCTL_OAUTH_LOOPBACK_URL:
            params = parse_qs(loc.query)

            if 'state' not in params or len(params['state']) != 1:
                return self.raise_error('state is missed')

            if 'code' not in params or len(params['code']) != 1:
                return self.raise_error('code is missed')

            state = params['state'][0]
            code = params['code'][0]

            if state != self.state:
                return self.raise_error(f'Wrong state. Received {state!r}, expected {self.state!r}')

            issue_token_url = get_oauth_token_issuer_url(self.target_url)
            if not issue_token_url:
                return self.raise_error(f'Can not get URL for issuing long-life token from {self.target_url}')

            login_result = get_id_token(code, issue_token_url, self.redirect_url)
            if not login_result:
                return self.raise_error(f'Failed to get long-life token from {issue_token_url}')

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            content = render_template('callback-response.html', {})
            self.wfile.write(content.encode('utf-8'))

            self.on_token_received(login_result)
        else:
            self.send_response(404)
            self.end_headers()


def handler_builder(on_token_received: typing.Callable[[OAuthLoginResult], None],
                    state: str, target_url: str, redirect_url: str) -> typing.Callable:
    """
    Create handler builder for OAuth2 callback built-in server

    :param on_token_received: callback that should be called on final auth. stage (when all tokens are received)
    :param state: randomly generated token for OAuth2 pipeline
    :param target_url: captured redirect to IP's URL
    :param redirect_url:  redirect URL to continue authorization
    :return: callable - handler builder function
    """
    def init(*args, **kwargs) -> object:
        """
        Builder (builds OAuth2Handler instance)

        :param args: system args
        :param kwargs: system args
        :return: object -- handler
        """
        OAuth2Handler(*args,
                      on_token_received=on_token_received,
                      state=state,
                      target_url=target_url,
                      redirect_url=redirect_url,
                      **kwargs)
    return init


def start_oauth2_callback_handler(on_token_received: typing.Callable[[OAuthLoginResult], None],
                                  state: str, target_url: str) -> str:
    """
    Start OAuth2 callback handler

    :param on_token_received: callback that should be called on final auth. stage (when all tokens are received)
    :param state: randomly generated token for OAuth2 pipeline
    :param target_url: captured redirect to IP's URL
    :return: str -- redirect URL to continue authorization
    """
    host = config.LEGIONCTL_OAUTH_LOOPBACK_HOST
    port = find_free_port(host)
    redirect_url = f'http://{config.LEGIONCTL_OAUTH_LOOPBACK_HOST}:{port}{config.LEGIONCTL_OAUTH_LOOPBACK_URL}'

    server = HTTPServer((host, port),
                        handler_builder(on_token_received, state, target_url, redirect_url))

    callback_handler = Thread(name='oauth2_callback_handler',
                              target=server.serve_forever)
    callback_handler.start()
    return redirect_url
