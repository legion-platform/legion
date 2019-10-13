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
import logging
import typing
from urllib import parse

from legion.sdk.clients.edi import RemoteEdiClient, AsyncRemoteEdiClient
from legion.sdk.definitions import MODEL_DEPLOYMENT_URL
from legion.sdk.models import ModelDeployment

LOGGER = logging.getLogger(__name__)

READY_STATE = "Ready"
PROCESSING_STATE = "Processing"
FAILED_STATE = "Failed"


class ModelDeploymentClient(RemoteEdiClient):
    """
    HTTP model deployment client
    """

    def get(self, name: str) -> ModelDeployment:
        """
        Get Model Deployment from EDI server

        :param name: Model Deployment name
        :return: Model Deployment
        """
        return ModelDeployment.from_dict(self.query(f'{MODEL_DEPLOYMENT_URL}/{name}'))

    def get_all(self, labels: typing.Dict[str, str] = None) -> typing.List[ModelDeployment]:
        """
        Get all Model Deployments from EDI server

        :return: all Model Deployments
        """
        if labels:
            url = f'{MODEL_DEPLOYMENT_URL}?{parse.urlencode(labels)}'
        else:
            url = MODEL_DEPLOYMENT_URL

        return [ModelDeployment.from_dict(md) for md in self.query(url)]

    def create(self, md: ModelDeployment) -> ModelDeployment:
        """
        Create Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return ModelDeployment.from_dict(
            self.query(MODEL_DEPLOYMENT_URL, action='POST', payload=md.to_dict())
        )

    def edit(self, md: ModelDeployment) -> ModelDeployment:
        """
        Edit Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return ModelDeployment.from_dict(
            self.query(MODEL_DEPLOYMENT_URL, action='PUT', payload=md.to_dict())
        )

    def delete(self, name: str) -> str:
        """
        Delete Model Deployments

        :param name: Name of a Model Deployment
        :return Message from EDI server
        """
        return self.query(f'{MODEL_DEPLOYMENT_URL}/{name}', action='DELETE')['message']


class AsyncModelDeploymentClient(AsyncRemoteEdiClient):
    """
    HTTP model deployment async client
    """

    async def get(self, name: str) -> ModelDeployment:
        """
        Get Model Deployment from EDI server

        :param name: Model Deployment name
        :return: Model Deployment
        """
        return ModelDeployment.from_dict(await self.query(f'{MODEL_DEPLOYMENT_URL}/{name}'))

    async def get_all(self, labels: typing.Dict[str, str] = None) -> typing.List[ModelDeployment]:
        """
        Get all Model Deployments from EDI server

        :return: all Model Deployments
        """
        if labels:
            url = f'{MODEL_DEPLOYMENT_URL}?{parse.urlencode(labels)}'
        else:
            url = MODEL_DEPLOYMENT_URL

        return [ModelDeployment.from_dict(md) for md in await self.query(url)]

    async def create(self, md: ModelDeployment) -> ModelDeployment:
        """
        Create Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return ModelDeployment.from_dict(
            await self.query(MODEL_DEPLOYMENT_URL, action='POST', payload=md.to_dict())
        )

    async def edit(self, md: ModelDeployment) -> ModelDeployment:
        """
        Edit Model Deployment

        :param md: Model Deployment
        :return Message from EDI server
        """
        return ModelDeployment.from_dict(
            await self.query(MODEL_DEPLOYMENT_URL, action='PUT', payload=md.to_dict())
        )

    async def delete(self, name: str) -> str:
        """
        Delete Model Deployments

        :param name: Name of a Model Deployment
        :return Message from EDI server
        """
        return await self.query(f'{MODEL_DEPLOYMENT_URL}/{name}', action='DELETE')['message']
