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
import json
import logging
from urllib.parse import urlparse
import typing

import requests
import requests.exceptions

from legion.sdk import config
from legion.sdk.containers import local_deploy
from legion.sdk.containers.docker import build_docker_client
from legion.sdk.definitions import EDI_VERSION, MODEL_TOKEN_TOKEN_URL

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


class RemoteEdiClient:
    """
    EDI client
    """

    def __init__(self, base, token=None, retries=3, timeout=10):
        """
        Build client

        :param base: base url, for example: http://edi.parallels
        :type base: str
        :param token: token for token based auth
        :type token: str or None
        :param retries: command retries or less then 2 if disabled
        :type retries: int
        :param timeout: timeout for connection in seconds. 0 for disabling
        :type timeout: int
        """
        self._base = base
        self._token = token
        self._version = EDI_VERSION
        self._retries = retries
        self._timeout = timeout

    @classmethod
    def construct_from_other(cls, other):
        """
        Construct EDI-based client from another EDI-based client

        :param other: EDI-based client to get connection options from
        :type other: RemoteEdiClient
        :return: self -- new client
        """
        return cls(other._base, other._token, other._retries, other._timeout)

    def _request(self, url_template: str, payload: typing.Mapping[typing.Any, typing.Any] = None, action: str = 'GET',
                 stream: bool = False, timeout: typing.Optional[int] = None):
        """
        Make HTTP request
        :param action: request action, e.g. get / post / delete
        :type action: str
        :param url: target URL
        :type url: str
        :param data: (Optional) data to be placed in body of request
        :type data: dict[str, str] or None
        :param headers: (Optional) additional HTTP headers
        :type headers: dict[str, str] or None
        :param cookies: (Optional) HTTP cookies
        :type cookies: dict[str, str] or None
        :param timeout: (Optional) custom timeout in seconds (overrides default). 0 for disabling
        :type timeout: typing.Optional[int]
        :return: :py:class:`requests.Response` -- response
        """
        sub_url = url_template.format(version=self._version)
        target_url = self._base.strip('/') + sub_url
        cookies = {'_oauth2_proxy': self._token} if self._token else {}

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
                    request_kwargs['headers'] = {'Content-type': 'text/event-stream'}

                response = requests.request(action.lower(), target_url, cookies=cookies, stream=stream,
                                            timeout=connection_timeout,
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

        # We assume if there were redirects then credentials are out of date
        if response.history:
            LOGGER.debug('Status code: "{}", Response: "{}"'.format(response.status_code, response.text))

            parse_result = urlparse(target_url)
            raise IncorrectAuthorizationToken(
                'Credentials are not correct. You should open {}://{} url in a browser to get fresh token'.format(
                    parse_result.scheme, parse_result.netloc
                )) from raised_exception

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
        :return: API Mmdel token
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


def build_client(args: argparse.Namespace = None) -> RemoteEdiClient:
    """
    Build Remote EDI client from from ENV and from command line arguments

    :param args: (optional) command arguments with .namespace
    """
    host, token = None, None

    if args:
        if args.edi:
            host = args.edi

        if args.token:
            token = args.token

    if not host or not token:
        host = host or config.EDI_URL
        token = token or config.EDI_TOKEN

    if host:
        client = RemoteEdiClient(host, token)
    else:
        raise Exception('EDI endpoint is not configured')

    return client
