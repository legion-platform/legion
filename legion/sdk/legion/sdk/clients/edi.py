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

    def __init__(self, status_code: int, http_result: typing.Dict[str, str]):
        """
        Wrong Http Status Code
        :param status_code: HTTP status code
        :param http_result: HTTP data
        """
        super().__init__(f'Got error from server: {http_result["message"]}')

        self.status_code = status_code


class RemoteEdiClient:
    """
    EDI client
    """

    def __init__(self, base, token=None, retries=3):
        """
        Build client

        :param base: base url, for example: http://edi.parallels
        :type base: str
        :param token: token for token based auth
        :type token: str or None
        :param retries: command retries or less then 2 if disabled
        :type retries: int
        """
        self._base = base
        self._token = token
        self._version = EDI_VERSION
        self._retries = retries

    def _request(self, action, url, data=None, headers=None, cookies=None):
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
        :return: :py:class:`requests.Response` -- response
        """
        return requests.request(action.lower(), url, headers=headers, cookies=cookies, json=data)

    def query(self, url_template, payload=None, action='GET'):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :type url_template: str
        :param payload: payload (will be converted to JSON) or None
        :type payload: dict[str, any]
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :type action: str
        :return: dict[str, any] -- response content
        """
        sub_url = url_template.format(version=self._version)
        target_url = self._base.strip('/') + sub_url
        cookies = {'_oauth2_proxy': self._token} if self._token else {}

        left_retries = self._retries if self._retries > 0 else 1
        raised_exception = None
        while left_retries > 0:
            try:
                LOGGER.debug('Requesting {}'.format(target_url))

                response = self._request(action, target_url, payload, cookies=cookies)
            except requests.exceptions.ConnectionError as exception:
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break

            left_retries -= 1
        else:
            raise Exception('Failed to connect to {}. No one retry left. Exception: {}'.format(
                self._base, raised_exception
            ))

        # We assume if there were redirects then credentials are out of date
        if response.history:
            LOGGER.debug('Status code: "{}", Response: "{}"'.format(response.status_code, response.text))

            parse_result = urlparse(target_url)

            raise Exception(
                'Credentials are not correct. You should open {}://{} url in a browser to get fresh token'.format(
                    parse_result.scheme, parse_result.netloc
                )
            )

        try:
            answer = json.loads(response.text)
            LOGGER.debug('Got answer: {!r} with code {} for URL {!r}'
                         .format(answer, response.status_code, target_url))
        except ValueError as json_decode_exception:
            raise ValueError('Invalid JSON structure {!r}: {}'.format(response.text, json_decode_exception))

        if not response.ok:
            raise WrongHttpStatusCode(response.status_code, answer)

        LOGGER.debug('Query has been completed, parsed and validated')
        return answer

    def get_token(self, model_id, model_version, expiration_date=None):
        """
        Get API token

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param expiration_date: utc datetime of the token expiration in format "%Y-%m-%dT%H:%M:%S"
        :type expiration_date: str
        :return: str -- return API Token
        """
        payload = {'model_id': model_id, 'model_version': model_version}

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
        :param model: (Optional) model id
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
        :param model: (Optional) model id
        :type model: str
        :param version: (Optional) model version
        :type version: str
        :param ignore_not_found: (Optional) ignore if cannot find models
        :type ignore_not_found: bool
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        client = build_docker_client()
        return local_deploy.undeploy_model(client, deployment_name, model, version, ignore_not_found)

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
                        default=300,
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
