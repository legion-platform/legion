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
EDI client
"""
import json
import logging
import random
import string
import sys
import threading
import typing

from urllib.parse import urlparse, urlencode
import requests
import requests.exceptions

import legion.sdk.config
from legion.sdk.clients.oauth_handler import start_oauth2_callback_handler, OAuthLoginResult, do_refresh_token
from legion.sdk.config import update_config_file
from legion.sdk.definitions import EDI_VERSION

LOGGER = logging.getLogger(__name__)


class WrongHttpStatusCode(Exception):
    """
    Exception for wrong HTTP status code
    """

    def __init__(self, status_code: int, http_result: typing.Dict[str, str] = None):
        """
        Initialize Wrong Http Status Code exception

        :param status_code: HTTP status code
        :param http_result: HTTP data
        """
        if http_result is None:
            http_result = {}
        super().__init__(f'Got error from server: {http_result.get("message")}')

        self.status_code = status_code


class EDIConnectionException(Exception):
    """
    Exception that says that client can not reach EDI server
    """

    pass


class IncorrectAuthorizationToken(EDIConnectionException):
    """
    Exception that says that provided EDI authorization token is incorrect
    """

    pass


def get_authorization_redirect(web_redirect: str, after_login: typing.Callable) -> str:
    """
    Try to detect, parse and build OAuth2 redirect

    :param web_redirect: returned redirect
    :param after_login: function that have to be called after successful login
    :return: str -- new redirect
    """
    loc = urlparse(web_redirect)

    state = ''.join(random.choice(string.ascii_letters) for _ in range(10))
    local_check_address = start_oauth2_callback_handler(after_login, state, web_redirect)

    get_parameters = {
        'client_id': legion.sdk.config.LEGIONCTL_OAUTH_CLIENT_ID,
        'response_type': 'code',
        'state': state,
        'redirect_uri': local_check_address,
        'scope': legion.sdk.config.LEGIONCTL_OAUTH_SCOPE
    }
    web_redirect = f'{loc.scheme}://{loc.netloc}{loc.path}?{urlencode(get_parameters)}'
    return web_redirect


class RemoteEdiClient:
    """
    Base EDI client
    """

    def __init__(self,
                 base_url: str = legion.sdk.config.EDI_URL,
                 token: typing.Optional[str] = legion.sdk.config.EDI_TOKEN,
                 retries: typing.Optional[int] = 3,
                 timeout: typing.Optional[int] = 10,
                 non_interactive: typing.Optional[bool] = True):
        """
        Build client

        :param base_url: base url, for example: http://edi.example.com
        :param token: token for token based auth
        :param retries: command retries or less then 2 if disabled
        :param timeout: timeout for connection in seconds. 0 for disabling
        :param non_interactive: disable any interaction
        """
        self._base_url = base_url
        self._token = token
        self._version = EDI_VERSION
        self._retries = retries
        self._timeout = timeout
        self._non_interactive = non_interactive
        self._interactive_login_finished = threading.Event()

        # Force if set
        if legion.sdk.config.LEGIONCTL_NONINTERACTIVE:
            self._non_interactive = True

    def _update_config_with_new_oauth_config(self, login_result: OAuthLoginResult) -> None:
        """
        Update config with new oauth credentials

        :param login_result: result of login
        :return: None
        """
        self._token = login_result.id_token
        update_config_file(EDI_URL=self._base_url,
                           EDI_TOKEN=login_result.id_token,
                           EDI_REFRESH_TOKEN=login_result.refresh_token,
                           EDI_ACCESS_TOKEN=login_result.access_token,
                           EDI_ISSUING_URL=login_result.issuing_url)

    def after_login(self, login_result: OAuthLoginResult) -> None:
        """
        Handle action after login

        :param login_result: result of login
        :return: None
        """
        self._interactive_login_finished.set()
        self._update_config_with_new_oauth_config(login_result)
        LOGGER.info('You has been authorized on endpoint %s as %s / %s',
                    self._base_url, login_result.user_name, login_result.user_email)
        sys.exit(0)

    @classmethod
    def construct_from_other(cls, other):
        """
        Construct EDI-based client from another EDI-based client

        :param other: EDI-based client to get connection options from
        :return: self -- new client
        """
        return cls(other._base_url, other._token, other._retries, other._timeout)

    def _request(self,
                 url_template: str,
                 payload: typing.Mapping[typing.Any, typing.Any] = None,
                 action: str = 'GET',
                 stream: bool = False,
                 timeout: typing.Optional[int] = None,
                 limit_stack: bool = False):
        """
        Make HTTP request

        :param url_template: target URL
        :param payload: data to be placed in body of request
        :param action: request action, e.g. get / post / delete
        :param stream: use stream mode or not
        :param timeout: custom timeout in seconds (overrides default). 0 for disabling
        :param limit_stack: do not start refreshing token if it is possible
        :return: :py:class:`requests.Response` -- response
        """
        sub_url = url_template.format(version=self._version)
        target_url = self._base_url.strip('/') + sub_url
        headers = {}

        # Add token if it is provided
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'
            credentials_error_status = 'Credentials are not correct'
        else:
            credentials_error_status = 'Credentials are missed'

        left_retries = self._retries if self._retries > 0 else 1

        connection_timeout = timeout if timeout is not None else self._timeout

        if connection_timeout == 0:
            connection_timeout = None

        if stream:
            connection_timeout = (connection_timeout, None)
        else:
            connection_timeout = connection_timeout

        raised_exception = None

        while left_retries > 0:
            try:
                LOGGER.debug('Requesting {}'.format(target_url))
                request_kwargs = {'params' if action.lower() == 'get' else 'json': payload}

                if stream:
                    headers['Content-type'] = 'text/event-stream'

                response = requests.request(action.lower(), target_url, stream=stream,
                                            timeout=connection_timeout,
                                            headers=headers,
                                            **request_kwargs)
            except requests.exceptions.ConnectionError as exception:
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base_url, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break

            left_retries -= 1
        else:
            raise EDIConnectionException('Can not reach {}'.format(self._base_url)) from raised_exception

        # We assume if there were redirects then credentials are out of date and we can refresh or build auth url
        if response.history:
            # If it is a error after refreshed token - fail
            if limit_stack:
                raise IncorrectAuthorizationToken(
                    f'{credentials_error_status} even after refreshing. \n'
                    'Please try to log in again'
                ) from raised_exception

            LOGGER.debug('Status code: "{}", Response: "{}"'.format(response.status_code, response.text))
            LOGGER.debug('Redirect has been detected. Trying to refresh a token')

            if legion.sdk.config.EDI_REFRESH_TOKEN and legion.sdk.config.EDI_ISSUING_URL:
                LOGGER.debug('Refresh token for %s has been found, trying to use it', legion.sdk.config.EDI_ISSUING_URL)
                login_result = do_refresh_token(legion.sdk.config.EDI_REFRESH_TOKEN, legion.sdk.config.EDI_ISSUING_URL)
                if not login_result:
                    raise IncorrectAuthorizationToken(
                        'Refresh token in not correct. \n'
                        'Please login again'
                    ) from raised_exception
                else:
                    self._update_config_with_new_oauth_config(login_result)
                    return self._request(
                        url_template,
                        payload=payload,
                        action=action,
                        stream=stream,
                        timeout=timeout,
                        limit_stack=True
                    )
            else:
                if self._non_interactive:
                    raise IncorrectAuthorizationToken(
                        f'{credentials_error_status}. \n'
                        'Please provide correct temporary token or disable non interactive mode'
                    ) from raised_exception
                else:
                    # Start interactive flow
                    self._interactive_login_finished.clear()
                    target_url = get_authorization_redirect(response.url, self.after_login)
                    LOGGER.error('%s. \nPlease open %s', credentials_error_status, target_url)

                    self._interactive_login_finished.wait()
                    return self._request(
                        url_template,
                        payload=payload,
                        action=action,
                        stream=stream,
                        timeout=timeout,
                        limit_stack=True
                    )

        return response

    def query(self, url_template: str, payload: typing.Mapping[typing.Any, typing.Any] = None, action: str = 'GET'):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :param payload: payload (will be converted to JSON) or None
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :return: dict[str, any] -- response content
        """
        response = self._request(url_template, payload, action)

        try:
            answer = json.loads(response.text)
            LOGGER.debug('Got answer: {!r} with code {} for URL {!r}'
                         .format(answer, response.status_code, payload))
        except ValueError as json_decode_exception:
            raise ValueError('Invalid JSON structure {!r}: {}'.format(response.text, json_decode_exception))

        if not response.ok:
            raise WrongHttpStatusCode(response.status_code, answer)

        LOGGER.debug('Query has been completed, parsed and validated')
        return answer

    def stream(self, url_template: str, action: str = 'GET',
               params: typing.Mapping[str, typing.Any] = None) -> typing.Dict[str, typing.Any]:
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :param params: payload (will be converted to JSON) or None
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :return: response content
        """
        response = self._request(url_template, action=action, stream=True, payload=params)

        with response:
            if not response.ok:
                raise WrongHttpStatusCode(response.status_code)

            for line in response.iter_lines():
                yield line.decode("utf-8")

    def info(self):
        """
        Perform info query on EDI server

        :return:
        """
        try:
            return self.query("/health")
        except ValueError:
            pass
