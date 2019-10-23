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
from collections import AsyncIterable
from typing import List, Iterator

from legion.sdk.clients.edi import RemoteEdiClient, AsyncRemoteEdiClient
from legion.sdk.definitions import MODEL_PACKING_URL
from legion.sdk.models import ModelPackaging

SCHEDULING_STATE = "scheduling"
RUNNING_STATE = "running"
SUCCEEDED_STATE = "succeeded"
FAILED_STATE = "failed"
UNKNOWN_STATE = "unknown"


class ModelPackagingClient(RemoteEdiClient):
    """
    Model Packaging client
    """

    def get(self, name: str) -> ModelPackaging:
        """
        Get Model Packaging from EDI server

        :param name: Model Packaging name
        :type name: str
        :return: Model Packaging
        """
        return ModelPackaging.from_dict(self.query(f'{MODEL_PACKING_URL}/{name}'))

    def get_all(self) -> List[ModelPackaging]:
        """
        Get all Model Packagings from EDI server

        :return: all Model Packagings
        """
        return [ModelPackaging.from_dict(mr) for mr in self.query(MODEL_PACKING_URL)]

    def create(self, mr: ModelPackaging) -> ModelPackaging:
        """
        Create Model Packaging

        :param mr: Model Packaging
        :return Message from EDI server
        """
        return ModelPackaging.from_dict(
            self.query(MODEL_PACKING_URL, action='POST', payload=mr.to_dict())
        )

    def edit(self, mr: ModelPackaging) -> ModelPackaging:
        """
        Edit Model Packaging

        :param mr: Model Packaging
        :return Message from EDI server
        """
        return ModelPackaging.from_dict(
            self.query(MODEL_PACKING_URL, action='PUT', payload=mr.to_dict())
        )

    def delete(self, name: str) -> str:
        """
        Delete Model Packagings

        :param name: Name of a Model Packaging
        :return Message from EDI server
        """
        return self.query(f'{MODEL_PACKING_URL}/{name}', action='DELETE')

    def log(self, name: str, follow: bool = False) -> Iterator[str]:
        """
        Stream logs from packaging

        :param follow: follow stream
        :param name: Name of a Model Packaging
        :return Message from EDI server
        """
        return self.stream(f'{MODEL_PACKING_URL}/{name}/log', 'GET', params={'follow': follow})


class AsyncModelPackagingClient(AsyncRemoteEdiClient, ModelPackagingClient):
    """
    Model Packaging async client
    """

    async def get(self, name: str) -> ModelPackaging:
        """
        Get Model Packaging from EDI server

        :param name: Model Packaging name
        :type name: str
        :return: Model Packaging
        """
        return ModelPackaging.from_dict(await self.query(f'{MODEL_PACKING_URL}/{name}'))

    async def get_all(self) -> List[ModelPackaging]:
        """
        Get all Model Packagings from EDI server

        :return: all Model Packagings
        """
        return [ModelPackaging.from_dict(mr) for mr in await self.query(MODEL_PACKING_URL)]

    async def create(self, mr: ModelPackaging) -> ModelPackaging:
        """
        Create Model Packaging

        :param mr: Model Packaging
        :return Message from EDI server
        """
        return ModelPackaging.from_dict(
            await self.query(MODEL_PACKING_URL, action='POST', payload=mr.to_dict())
        )

    async def edit(self, mr: ModelPackaging) -> ModelPackaging:
        """
        Edit Model Packaging

        :param mr: Model Packaging
        :return Message from EDI server
        """
        return ModelPackaging.from_dict(
            await self.query(MODEL_PACKING_URL, action='PUT', payload=mr.to_dict())
        )

    async def delete(self, name: str) -> str:
        """
        Delete Model Packagings

        :param name: Name of a Model Packaging
        :return Message from EDI server
        """
        return await self.query(f'{MODEL_PACKING_URL}/{name}', action='DELETE')

    async def log(self, name: str, follow: bool = False) -> AsyncIterable:
        """
            Stream logs from packaging

            :param follow: follow stream
            :param name: Name of a Model Packaging
            :return Message from EDI server
            """
        params = {'follow': 'true' if follow else 'false'}
        async for chunk in self.stream(f'{MODEL_PACKING_URL}/{name}/log', 'GET', params=params):
            yield chunk
