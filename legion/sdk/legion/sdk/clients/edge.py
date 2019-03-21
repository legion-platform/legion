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
EDGE client
"""
import abc
import argparse
import logging
import typing

import requests

from legion.sdk import config
from legion.sdk.containers.docker import build_docker_client, find_host_model_port
from legion.sdk import definitions
from legion.sdk.utils import normalize_name

LOGGER = logging.getLogger(__name__)


class EdgeClient(metaclass=abc.ABCMeta):
    """
    Base EDGE client
    """

    @abc.abstractmethod
    def invoke_model_api(self, model_id: str, model_version: str, payload: typing.Dict[str, typing.Any],
                         endpoint: str = 'default') -> typing.Any:
        """
        Perform inspect query on EDGE server

        :param model_id: model ID
        :param model_version: model version
        :param endpoint: name of endpoint
        :param payload: payload
        :return: json model response
        """
        pass


class RemoteEdgeClient(EdgeClient):
    """
    EDGE client
    """

    def __init__(self, model_server_url: str, jwt: str) -> None:
        """
        Build RemoteEdgeClient

        :param model_server_url: edge url
        :param jwt: model jwt token
        """
        if not model_server_url:
            raise ValueError('Please, specify model server url')
        if not jwt:
            raise ValueError('Please, specify model jwt')

        self._model_server_url = model_server_url
        self._jwt = jwt

    def invoke_model_api(self, model_id: str, model_version: str, payload: typing.Dict[str, typing.Any],
                         endpoint: str = 'default') -> typing.Any:
        """
        Perform inspect query on EDGE server

        :param model_id: model ID
        :param model_version: model version
        :param endpoint: name of endpoint
        :param payload: payload
        :return: json model response
        """
        headers = {'Authorization': f'Bearer {self._jwt}'}

        url = f'{self._model_server_url}/api/model/{model_id}/{model_version}/invoke/{endpoint}'

        LOGGER.debug('Requesting {} with data = {} in POST mode'.format(url, payload))

        response = requests.post(
            url,
            data=payload,
            headers=headers
        )

        if response.status_code == 401:
            raise Exception('Wrong jwt model token. You can refresh it by using "legionctl generate-token" command')

        if not response.ok:
            raise Exception(f'Returned wrong status code: {response.status_code}, text: {response.text}')

        return response.json()


class LocalEdgeClient(EdgeClient):

    def invoke_model_api(self, model_id: str, model_version: str, payload: typing.Dict[str, typing.Any],
                         endpoint: str = 'default') -> typing.Any:
        """
        Perform inspect query on EDGE server

        :param model_id: model ID
        :param model_version: model version
        :param endpoint: name of endpoint
        :param payload: payload
        :return: json model response
        """
        client = build_docker_client()
        containers = client.containers.list(filters={
            'label': [f'{definitions.LEGION_COMPONENT_LABEL}.model_id={model_id}',
                      f'{definitions.LEGION_COMPONENT_LABEL}.model_version={model_version}']
        })

        if not containers:
            raise ValueError(
                f'Can not find container with {model_id} model id and {model_version} model version labels')

        if len(containers) > 1:
            raise ValueError(
                f'Find multiple containers with {model_id} model id and {model_version} model version labels')

        model_port = find_host_model_port(containers[0])

        url = f'http://localhost:{model_port}/api/model/{model_id}/{model_version}/invoke/{endpoint}'
        response = requests.post(
            url,
            data=payload
        )

        if not response.ok:
            raise Exception(f'Returned wrong status code: {response.status_code}, text: {response.text}')

        return response.json()


def model_config_prefix(model_id: str, model_version: str) -> str:
    """
    Build model prefix for the cli config
    :param model_id: model id
    :param model_version: model version
    :return: config prefix
    """
    return normalize_name(f'{model_id}-{model_version}')


def build_client(args: argparse.Namespace = None) -> EdgeClient:
    """
    Build EDGE client from from ENV and from command line arguments

    :param args: (optional) command arguments with .namespace
    :return: EDGE client
    """
    host, token = None, None

    if args:
        if 'local' in args and args.local:
            return LocalEdgeClient()

        if args.model_server_url:
            host = args.model_server_url

        if args.jwt:
            token = args.jwt

    host = host or config.MODEL_SERVER_URL
    token = token or config.get_config_file_variable(model_config_prefix(args.model_id, args.model_version),
                                                     section=config.MODEL_JWT_TOKEN_SECTION)

    return RemoteEdgeClient(host, token)
