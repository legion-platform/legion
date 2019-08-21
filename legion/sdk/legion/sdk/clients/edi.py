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
import argparse
import random
import json
import logging
from urllib.parse import urlparse, urlencode
import typing
import threading
import string
import sys

import requests
import requests.exceptions

import legion.sdk.config
from legion.sdk.config import update_config_file
from legion.sdk.containers import local_deploy
from legion.sdk.containers.docker import build_docker_client
from legion.sdk.definitions import EDI_VERSION, MODEL_TOKEN_TOKEN_URL
from legion.sdk.clients.oauth_handler import start_oauth2_callback_handler, OAuthLoginResult, do_refresh_token

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
    EDI client
    """

    def __init__(self, base, token=None, retries=3, timeout=10, non_interactive=False):
        """
        Build client

        :param base: base url, for example: http://edi.example.com
        :type base: str
        :param token: (Optional) token for token based auth
        :type token: str or None
        :param retries: (Optional) command retries or less then 2 if disabled
        :type retries: int
        :param timeout: (Optional) timeout for connection in seconds. 0 for disabling
        :type timeout: int
        :param non_interactive: (Optional) disable any interaction
        :type non_interactive: book
        """
        self._base = base
        self._token = token
        self._version = EDI_VERSION
        self._retries = retries
        self._timeout = timeout
        self._non_interactive = non_interactive
        self._interactive_login_finished = threading.Event()

        # Force if set
        if legion.sdk.config.LEGIONCTL_NONINTERACTIVE:
            self._non_interactive = True

    def _update_config_with_new_oauth_config(self, login_result: OAuthLoginResult):
        """
        Update config with new oauth credentials

        :param login_result: result of login
        :type login_result: OAuthLoginResult
        :return: None
        """
        self._token = login_result.id_token
        update_config_file(EDI_URL=self._base,
                           EDI_TOKEN=login_result.id_token,
                           EDI_REFRESH_TOKEN=login_result.refresh_token,
                           EDI_ACCESS_TOKEN=login_result.access_token,
                           EDI_ISSUING_URL=login_result.issuing_url)

    def after_login(self, login_result: OAuthLoginResult):
        """
        Handle action after login

        :param login_result: result of login
        :type login_result: OAuthLoginResult
        :return: None
        """
        self._interactive_login_finished.set()
        self._update_config_with_new_oauth_config(login_result)
        LOGGER.info('You has been authorized on endpoint %s as %s / %s',
                    self._base, login_result.user_name, login_result.user_email)
        sys.exit(0)

    @classmethod
    def construct_from_other(cls, other):
        """
        Construct EDI-based client from another EDI-based client

        :param other: EDI-based client to get connection options from
        :type other: RemoteEdiClient
        :return: self -- new client
        """
        return cls(other._base, other._token, other._retries, other._timeout)

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
        :type url_template: str
        :param payload: (Optional) data to be placed in body of request
        :type payload: dict[str, str] or None
        :param action: request action, e.g. get / post / delete
        :type action: str
        :param stream: (Optional) use stream mode or not
        :type stream: bool
        :param timeout: (Optional) custom timeout in seconds (overrides default). 0 for disabling
        :type timeout: typing.Optional[int]
        :param limit_stack: (Optional) do not start refreshing token if it is possible
        :type limit_stack: bool
        :return: :py:class:`requests.Response` -- response
        """
        sub_url = url_template.format(version=self._version)
        target_url = self._base.strip('/') + sub_url
        headers = {}

        # Add token if it is provided
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'

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
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break

            left_retries -= 1
        else:
            raise EDIConnectionException('Can not reach {}'.format(self._base)) from raised_exception

        # We assume if there were redirects then credentials are out of date and we can refresh or build auth url
        if response.history:
            # If it is a error after refreshed token - fail
            if limit_stack:
                raise IncorrectAuthorizationToken(
                    'Credentials are not correct even after refreshing. \n'
                    'Please login again'
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
                        'Credentials are not correct. \n'
                        'Please provide correct temporary token or disable non interactive mode'
                    ) from raised_exception
                else:
                    # Start interactive flow
                    self._interactive_login_finished.clear()
                    target_url = get_authorization_redirect(response.url, self.after_login)
                    LOGGER.error('Credentials are not correct. \nPlease open %s', target_url)

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

    def stream(self, url_template: str, action: str = 'GET', params: typing.Mapping[str, typing.Any] = None):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :param params: payload (will be converted to JSON) or None
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :return: dict[str, any] -- response content
        """
        response = self._request(url_template, action=action, stream=True, payload=params)

        with response:
            if not response.ok:
                raise WrongHttpStatusCode(response.status_code)

            for line in response.iter_lines():
                yield line.decode("utf-8")

    def get_token(self, md_role_name: str, expiration_date: typing.Optional[str] = None) -> str:
        """
        Get API token

        :param md_role_name: model name
        :param expiration_date: utc datetime of the token expiration in format "%Y-%m-%dT%H:%M:%S"
        :return: str -- API Model token
        """
        payload = {'role_name': md_role_name}

        if expiration_date:
            payload['expiration_date'] = expiration_date

        response = self.query(MODEL_TOKEN_TOKEN_URL, action='POST', payload=payload)
        if response and 'token' in response:
            return response['token']

    def info(self):
        """
        Perform info query on EDI server

        :return:
        """
        try:
            return self.query("/health")
        except ValueError:
            pass


class LocalEdiClient:

    def inspect(self, deployment_name=None, model=None, version=None):
        """
        Perform inspect query on EDI server

        :param deployment_name: (Optional) name of deployment
        :type deployment_name: str
        :param model: (Optional) model name
        :type model: str
        :param version: (Optional) model version
        :type version: str
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
        """
        client = build_docker_client()
        return local_deploy.get_models(client, deployment_name, model, version)

    def deploy(self, deployment_name, image, local_port=None):
        """
        Deploy API endpoint

        :param deployment_name: name of deployment
        :type deployment_name: str
        :param image: Docker image for deploy (for kubernetes deployment and local pull)
        :type image: str
        :param local_port: (Optional) port to deploy model on (for local mode deploy)
        :type local_port: int
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        client = build_docker_client()
        return local_deploy.deploy_model(client, deployment_name, image, local_port=local_port)

    def undeploy(self, deployment_name=None, model=None, version=None, ignore_not_found=False):
        """
        Undeploy API endpoint

        :param deployment_name: (Optional) name of deployment
        :type deployment_name: str
        :param model: (Optional) model name
        :type model: str
        :param version: (Optional) model version
        :type version: str
        :param ignore_not_found: (Optional) ignore if cannot find models
        :type ignore_not_found: bool
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        client = build_docker_client()
        return local_deploy.undeploy_model(client, deployment_name, model, version, ignore_not_found)

    def get_builds(self):
        """
        Get available builds

        :return: list[:py:class:`legion.containers.definitions.ModelBuildInformation`] -- registered model builds
        """
        client = build_docker_client()
        return local_deploy.get_local_builds(client)

    def __repr__(self):
        """
        Get string representation of object

        :return: str -- string representation
        """
        return 'LocalEdiClient()'

    __str__ = __repr__


def add_arguments_for_wait_operation(parser):
    """
    Add arguments of wait operation in the parser

    :param parser: add arguments to it
    :type parser: argparse.ArgumentParser
    :return: None
    """
    parser.add_argument('--no-wait',
                        action='store_true', help='no wait until scale will be finished')
    parser.add_argument('--timeout',
                        default=600,
                        type=int, help='timeout in s. for wait (if no-wait is off)')


def build_client(args: argparse.Namespace = None, retries=3, timeout=10, cls=RemoteEdiClient):
    """
    Build Remote EDI client from from ENV and from command line arguments

    :param args: (optional) command arguments with .namespace
    :param retries: number of retries
    :param timeout: request timeout in seconds
    :param cls: target class
    """
    host, token, non_interactive = None, None, False

    if args:
        if args.edi:
            host = args.edi

        if args.token:
            token = args.token

        if args.non_interactive:
            non_interactive = True

    if not host or not token:
        host = host or legion.sdk.config.EDI_URL
        token = token or legion.sdk.config.EDI_TOKEN

    if host:
        client = cls(host, token, non_interactive=non_interactive, retries=retries, timeout=timeout)
    else:
        raise Exception('EDI endpoint is not configured')

    return client
