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
from urllib import parse

import legion.sdk.clients.edi
from legion.sdk.definitions import MODEL_DEPLOYMENT_URL

LOGGER = logging.getLogger(__name__)

READY_STATE = "Ready"
PROCESSING_STATE = "Processing"
FAILED_STATE = "Failed"


class ModelDeployment(typing.NamedTuple):
    name: str
    image: str
    role_name: str = ""
    resources: typing.Mapping[str, typing.Any] = {}
    annotations: typing.Mapping[str, str] = {}
    min_replicas: int = 0
    max_replicas: int = 1
    liveness_probe_initial_delay: int = 3
    readiness_probe_initial_delay: int = 3
    state: str = ""
    service_url: str = ""
    available_replicas: int = 0
    replicas: int = 0

    @staticmethod
    def from_json(md: typing.Dict[str, str]) -> 'ModelDeployment':
        """
        Convert raw dict from EDI to Model Deployment
        :param md: raw dict
        :return: a Model Deployment
        """
        md_spec = md.get('spec', {})
        md_metadata = md.get('metadata', {})
        md_status = md.get('status', {})

        return ModelDeployment(
            name=md.get('name', md_metadata.get('name', '')),
            image=md_spec.get('image', ''),
            resources=md_spec.get('resources', {}),
            annotations=md_spec.get('annotations', {}),
            role_name=md_spec.get('roleName', ''),
            min_replicas=int(md_spec.get('minReplicas', 0)),
            max_replicas=int(md_spec.get('maxReplicas', 1)),
            liveness_probe_initial_delay=md_spec.get('livenessProbeInitialDelay'),
            readiness_probe_initial_delay=md_spec.get('readinessProbeInitialDelay'),
            state=md_status.get('state', ''),
            service_url=md_status.get('serviceURL', ''),
            available_replicas=int(md_status.get('availableReplicas', 0)),
            replicas=int(md_status.get('replicas', 0)),
        )

    def to_json(self, with_status=False) -> typing.Dict[str, str]:
        """
        Convert a Model Deployment to raw json
        :return: raw dict
        """
        result = {
            'name': self.name,
            'spec': {
                'image': self.image,
                'resources': self.resources,
                'annotations': self.annotations,
                'minReplicas': self.min_replicas,
                'roleName': self.role_name,
                'maxReplicas': self.max_replicas,
                'livenessProbeInitialDelay': self.liveness_probe_initial_delay,
                'readinessProbeInitialDelay': self.readiness_probe_initial_delay
            }
        }
        if with_status:
            result['status'] = {
                'state': self.state,
                'serviceURL': self.service_url,
                'availableReplicas': self.available_replicas,
                'replicas': self.replicas
            }
        return result


class ModelDeploymentClient(legion.sdk.clients.edi.RemoteEdiClient):
    """
    EDI client
    """

    def get(self, name: str) -> ModelDeployment:
        """
        Get Model Deployment from EDI server

        :param name: Model Deployment name
        :return: Model Deployment
        """
        return ModelDeployment.from_json(self.query(f'{MODEL_DEPLOYMENT_URL}/{name}'))

    def get_all(self, labels: typing.Dict[str, str] = None) -> typing.List[ModelDeployment]:
        """
        Get all Model Deployments from EDI server

        :return: all Model Deployments
        """
        if labels:
            url = f'{MODEL_DEPLOYMENT_URL}?{parse.urlencode(labels)}'
        else:
            url = MODEL_DEPLOYMENT_URL

        return [ModelDeployment.from_json(md) for md in self.query(url)]

    def create(self, md: ModelDeployment) -> str:
        """
        Create Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return self.query(MODEL_DEPLOYMENT_URL, action='POST', payload=md.to_json())['message']

    def edit(self, md: ModelDeployment) -> str:
        """
        Edit Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return self.query(MODEL_DEPLOYMENT_URL, action='PUT', payload=md.to_json())['message']

    def delete(self, name: str) -> str:
        """
        Delete Model Deployments

        :param name: Name of a Model Deployment
        :return Message from EDI server
        """
        return self.query(f'{MODEL_DEPLOYMENT_URL}/{name}', action='DELETE')['message']

    def delete_all(self, labels: typing.Dict[str, str]) -> str:
        """
        Delete Model Deployments by labels

        :param labels: labels of a Model Deployment
        :return Message from EDI server
        """
        if labels:
            url = f'{MODEL_DEPLOYMENT_URL}?{parse.urlencode(labels)}'
        else:
            url = MODEL_DEPLOYMENT_URL

        return self.query(url, action='DELETE')['message']


def build_client(args: argparse.Namespace = None, retries=3, timeout=10) -> ModelDeploymentClient:
    """
    Build Model Deployment client from from ENV and from command line arguments

    :param timeout: request timeout in seconds
    :param retries: number of retries
    :param args: (optional) command arguments with .namespace
    """
    return legion.sdk.clients.edi.build_client(args, retries=retries, timeout=timeout, cls=ModelDeploymentClient)
