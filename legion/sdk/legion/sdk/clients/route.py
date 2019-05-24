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
import logging
import typing

from legion.sdk import config
from legion.sdk.clients.edi import RemoteEdiClient
from legion.sdk.definitions import MODEL_ROUTE_URL

LOGGER = logging.getLogger(__name__)

READY_STATE = "Ready"
PROCESSING_STATE = "Processing"


class ModelDeploymentTarget(typing.NamedTuple):
    name: str
    weight: typing.Optional[int] = None

    def to_json(self) -> typing.Dict[str, int]:
        """
        Convert a Model Deployment Target to raw json
        :return: raw dict
        """
        return {'name': self.name, 'weight': self.weight}


class ModelRoute(typing.NamedTuple):
    name: str
    url_prefix: str
    model_deployment_targets: typing.List[ModelDeploymentTarget]
    mirror: typing.Optional[str] = None
    edge_url: typing.Optional[str] = ""
    state: typing.Optional[str] = ""

    @staticmethod
    def from_json(mr: typing.Dict[str, str]) -> 'ModelRoute':
        """
        Convert raw dict from EDI to Model Route
        :param mr: raw dict
        :return: a Model Route
        """
        mr_metadata = mr.get('metadata', {})
        mr_spec = mr.get('spec', {})
        mr_status = mr.get('status', {})
        return ModelRoute(
            name=mr.get('name', mr_metadata.get('name', '')),
            url_prefix=mr_spec.get('urlPrefix', ''),
            model_deployment_targets=list(
                map(lambda x: ModelDeploymentTarget(x['name'], x['weight']), mr_spec.get('modelDeployments', []))),
            mirror=mr_spec.get('mirror', ''),
            edge_url=mr_status.get('edgeUrl', ''),
            state=mr_status.get('state', '')
        )

    def to_json(self, with_status=False) -> typing.Dict[str, str]:
        """
        Convert a Model Route to raw json
        :return: raw dict
        """
        result = {
            'name': self.name,
            'spec': {
                'urlPrefix': self.url_prefix,
                'modelDeployments': [x.to_json() for x in self.model_deployment_targets],
                'mirror': self.mirror,
            }
        }
        print(result)
        if with_status:
            result['status'] = {
                'edgeUrl': self.edge_url,
                'state': self.state
            }
        return result


class ModelRouteClient(RemoteEdiClient):
    """
    EDI client
    """

    def get(self, name: str) -> ModelRoute:
        """
        Get Model Route from EDI server

        :param name: Model Route name
        :type version: str
        :return: Model Route
        """
        return ModelRoute.from_json(self.query(f'{MODEL_ROUTE_URL}/{name}'))

    def get_all(self) -> typing.List[ModelRoute]:
        """
        Get all Model Routes from EDI server

        :return: all Model Routes
        """
        return [ModelRoute.from_json(mr) for mr in self.query(MODEL_ROUTE_URL)]

    def create(self, mr: ModelRoute) -> str:
        """
        Create Model Route

        :param mr: Model Route
        :return Message from EDI server
        """
        return self.query(MODEL_ROUTE_URL, action='POST', payload=mr.to_json())['message']

    def edit(self, mr: ModelRoute) -> str:
        """
        Edit Model Route

        :param mr: Model Route
        :return Message from EDI server
        """
        return self.query(MODEL_ROUTE_URL, action='PUT', payload=mr.to_json())['message']

    def delete(self, name: str) -> str:
        """
        Delete Model Routes

        :param name: Name of a Model Route
        :return Message from EDI server
        """
        return self.query(f'{MODEL_ROUTE_URL}/{name}', action='DELETE')['message']

    def delete_all(self) -> str:
        """
        Delete Model Routes by labels

        :param labels: labels of a Model Route
        :return Message from EDI server
        """
        return self.query(MODEL_ROUTE_URL, action='DELETE')['message']


def build_client(args: argparse.Namespace = None) -> ModelRouteClient:
    """
    Build Model Route client from from ENV and from command line arguments

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
        client = ModelRouteClient(host, token)
    else:
        raise Exception('EDI endpoint is not configured')

    return client
