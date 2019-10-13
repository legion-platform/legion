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
from typing import Mapping, Any, Optional, Iterator, Tuple, Union, Dict, Callable

from urllib.parse import urlparse, urlencode
import requests
import requests.exceptions
import httpx

import legion.sdk.config
from legion.sdk.clients.oauth_handler import start_oauth2_callback_handler, OAuthLoginResult, do_refresh_token
from legion.sdk.config import update_config_file
from legion.sdk.definitions import EDI_VERSION

LOGGER = logging.getLogger(__name__)


class WrongHttpStatusCode(Exception):
    """
    Exception for wrong HTTP status code
    """

    def __init__(self, status_code: int, http_result: Dict[str, str] = None):
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


def get_authorization_redirect(web_redirect: str, after_login: Callable) -> str:
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


def get_prepared_request(*args, **kwargs):
    request = requests.PreparedRequest()
    request.prepare(*args, **kwargs)
    return request


class RemoteEdiClient:
    """
    Base EDI client
    """

    def __init__(self,
                 base_url: str = legion.sdk.config.EDI_URL,
                 token: Optional[str] = legion.sdk.config.EDI_TOKEN,
                 retries: Optional[int] = 3,
                 timeout: Optional[Union[int, Tuple[int, int]]] = 10,
                 non_interactive: Optional[bool] = True):
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
        self._non_interactive = non_interactive
        self._interactive_login_finished = threading.Event()

        self.timeout = timeout
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
        return cls(other._base_url, other._token, other._retries, other.timeout)

    def _build_request(self,
                       request_cls,
                       url_template: str,
                       payload: Mapping[Any, Any] = None,
                       action: str = 'GET',
                       stream: bool = False):
        sub_url = url_template.format(version=self._version)
        target_url = self._base_url.strip('/') + sub_url
        headers = {}
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'
        if stream:
            headers['Content-type'] = 'text/event-stream'

        request_kwargs = {'params' if action.lower() == 'get' else 'json': payload}

        return request_cls(action.lower(), target_url, headers=headers, **request_kwargs)

    def _get_conn_timeout(self, timeout):
        connection_timeout = timeout if timeout is not None else self.timeout

        if connection_timeout == 0:
            connection_timeout = None

        return connection_timeout

    def _get_left_retries(self):
        return self._retries if self._retries > 0 else 1

    def _request(self,
                 url_template: str,
                 payload: Mapping[Any, Any] = None,
                 action: str = 'GET',
                 stream: bool = False,
                 timeout: Optional[int] = None,
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

        request = self._build_request(get_prepared_request, url_template, payload, action, stream)
        connection_timeout = self._get_conn_timeout(timeout)
        left_retries = self._get_left_retries()

        raised_exception = None
        while left_retries > 0:
            try:
                LOGGER.debug('Requesting {}'.format(request.url))

                with requests.Session() as client:
                    response = client.send(request, timeout=connection_timeout, stream=stream)
                    LOGGER.debug('Status code: "{}", Response: "{}"'.format(response.status_code, response.text))

            except requests.exceptions.ConnectionError as exception:
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base_url, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break
            left_retries -= 1
        else:
            raise EDIConnectionException('Can not reach {}'.format(self._base_url)) from raised_exception

        if self._login_required(response):
            try:
                self._login(str(response.url), limit_stack=limit_stack)
            except IncorrectAuthorizationToken as login_exc:
                raise login_exc from raised_exception
            return self._request(
                url_template,
                payload=payload,
                action=action,
                stream=stream,
                timeout=timeout,
                limit_stack=True
            )
        else:
            return response

    def query(self, url_template: str, payload: Mapping[Any, Any] = None, action: str = 'GET'):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :param payload: payload (will be converted to JSON) or None
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :return: dict[str, any] -- response content
        """
        response = self._request(url_template, payload, action)
        return self._handle_query_response(response, payload)

    @staticmethod
    def _handle_query_response(response, payload):

        try:
            answer = json.loads(response.text)
            LOGGER.debug('Got answer: {!r} with code {} for URL {!r}'
                         .format(answer, response.status_code, payload))
        except ValueError as json_decode_exception:
            raise ValueError('Invalid JSON structure {!r}: {}'.format(response.text, json_decode_exception))

        if 400 <= response.status_code < 600:
            raise WrongHttpStatusCode(response.status_code, answer)

        LOGGER.debug('Query has been completed, parsed and validated')
        return answer

    def stream(self, url_template: str, action: str = 'GET', params: Mapping[str, Any] = None) -> Iterator[str]:
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

    ############################
    # EDI login helper methods #
    ############################

    @staticmethod
    def _login_required(response: Union[httpx.AsyncResponse, httpx.Response]):
        """
        Check whether the login is required or client is already is authorised
        :param response:
        :return:
        """
        # We assume if there were redirects then credentials are out of date and we can refresh or build auth url
        if response.history:
            return True
        else:
            return False

    def _login(self, url: str, limit_stack=False):
        """
        Authorise client. Next methods are used by priority:
        1. Refreshing token (if token exists)
        2. Interactive mode (if enabled)
        :return: None if success, IncorrectAuthorizationToken exception otherwise
        """

        # If it is a error after refreshed token - fail
        if limit_stack:
            raise IncorrectAuthorizationToken(
                f'{self._credentials_error_status} even after refreshing. \n'
                'Please try to log in again'
            )

        LOGGER.debug('Redirect has been detected. Trying to refresh a token')
        if self._refresh_token_exists:
            LOGGER.debug('Refresh token for %s has been found, trying to use it', legion.sdk.config.EDI_ISSUING_URL)
            self._login_with_refresh_token()
        elif self._interactive_mode_enabled:
            # Start interactive flow
            self._login_interactive_mode(url)
        else:
            raise IncorrectAuthorizationToken(
                f'{self._credentials_error_status}. \n'
                'Please provide correct temporary token or disable non interactive mode'
            )

    def _login_with_refresh_token(self):
        login_result = do_refresh_token(legion.sdk.config.EDI_REFRESH_TOKEN, legion.sdk.config.EDI_ISSUING_URL)
        if not login_result:
            raise IncorrectAuthorizationToken(
                'Refresh token in not correct. \n'
                'Please login again'
            )
        else:
            self._update_config_with_new_oauth_config(login_result)

    def _login_interactive_mode(self, url):
        self._interactive_login_finished.clear()
        target_url = get_authorization_redirect(url, self.after_login)
        LOGGER.error('%s. \nPlease open %s', self._credentials_error_status, target_url)
        self._interactive_login_finished.wait()

    @property
    def _refresh_token_exists(self):
        return legion.sdk.config.EDI_REFRESH_TOKEN and legion.sdk.config.EDI_ISSUING_URL

    @property
    def _interactive_mode_enabled(self):
        return not self._non_interactive

    @property
    def _credentials_error_status(self):
        if self._token:
            credentials_error_status = 'Credentials are not correct'
        else:
            credentials_error_status = 'Credentials are missed'
        return credentials_error_status


class AsyncRemoteEdiClient(RemoteEdiClient):

    async def query(self, url_template: str, payload: Mapping[Any, Any] = None, action: str = 'GET'):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :param payload: payload (will be converted to JSON) or None
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :return: dict[str, any] -- response content
        """
        response = await self._request(url_template, payload, action)
        return self._handle_query_response(response, payload)

    async def _request(self, url_template: str,
                       payload: Mapping[Any, Any] = None,
                       action: str = 'GET',
                       stream: bool = False,
                       timeout: Optional[int] = None,
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
        request = self._build_request(httpx.AsyncRequest, url_template, payload, action, stream)
        connection_timeout = self._get_conn_timeout(timeout)
        left_retries = self._get_left_retries()

        raised_exception = None
        while left_retries > 0:
            try:
                LOGGER.debug('Requesting {}'.format(request.url))

                async with httpx.AsyncClient() as client:
                    response = await client.send(request, timeout=connection_timeout, stream=stream)
                    LOGGER.debug('Status code: "{}", Response: "{}"'.format(response.status_code, response.text))

            except requests.exceptions.ConnectionError as exception:
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base_url, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break
            left_retries -= 1
        else:
            raise EDIConnectionException('Can not reach {}'.format(self._base_url)) from raised_exception

        if self._login_required(response):
            try:
                self._login(str(response.url), limit_stack=limit_stack)
            except IncorrectAuthorizationToken as login_exc:
                raise login_exc from raised_exception
            return self._request(
                url_template,
                payload=payload,
                action=action,
                stream=stream,
                timeout=timeout,
                limit_stack=True
            )
        else:
            return response
