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
import typing

from legion.sdk.clients.edi import RemoteEdiClient, AsyncRemoteEdiClient
from legion.sdk.definitions import TOOLCHAIN_INTEGRATION_URL
from legion.sdk.models import ToolchainIntegration


class ToolchainIntegrationClient(RemoteEdiClient):
    """
    HTTP toolchain integration client
    """

    def get(self, name: str) -> ToolchainIntegration:
        """
        Get Toolchain Integration from EDI server

        :param name: Toolchain Integration name
        :type name: str
        :return: Toolchain Integration
        """
        return ToolchainIntegration.from_dict(self.query(f'{TOOLCHAIN_INTEGRATION_URL}/{name}'))

    def get_all(self) -> typing.List[ToolchainIntegration]:
        """
        Get all Toolchain Integrations from EDI server

        :return: all Toolchain Integrations
        """
        return [ToolchainIntegration.from_dict(ti) for ti in self.query(TOOLCHAIN_INTEGRATION_URL)]

    def create(self, ti: ToolchainIntegration) -> ToolchainIntegration:
        """
        Create Toolchain Integration

        :param ti: Toolchain Integration
        :return Message from EDI server
        """
        return ToolchainIntegration.from_dict(
            self.query(TOOLCHAIN_INTEGRATION_URL, action='POST', payload=ti.to_dict())
        )

    def edit(self, ti: ToolchainIntegration) -> ToolchainIntegration:
        """
        Edit Toolchain Integration

        :param ti: Toolchain Integration
        :return Message from EDI server
        """
        return ToolchainIntegration.from_dict(
            self.query(TOOLCHAIN_INTEGRATION_URL, action='PUT', payload=ti.to_dict())
        )

    def delete(self, name: str) -> str:
        """
        Delete Toolchain Integrations

        :param name: Name of a Toolchain Integration
        :return Message from EDI server
        """
        return self.query(f'{TOOLCHAIN_INTEGRATION_URL}/{name}', action='DELETE')


class AsyncToolchainIntegrationClient(AsyncRemoteEdiClient):
    """
    HTTP toolchain integration async client
    """
    async def get(self, name: str) -> ToolchainIntegration:
        """
        Get Toolchain Integration from EDI server

        :param name: Toolchain Integration name
        :type name: str
        :return: Toolchain Integration
        """
        return ToolchainIntegration.from_dict(await self.query(f'{TOOLCHAIN_INTEGRATION_URL}/{name}'))

    async def get_all(self) -> typing.List[ToolchainIntegration]:
        """
        Get all Toolchain Integrations from EDI server

        :return: all Toolchain Integrations
        """
        return [ToolchainIntegration.from_dict(ti) for ti in await self.query(TOOLCHAIN_INTEGRATION_URL)]

    async def create(self, ti: ToolchainIntegration) -> ToolchainIntegration:
        """
        Create Toolchain Integration

        :param ti: Toolchain Integration
        :return Message from EDI server
        """
        return ToolchainIntegration.from_dict(
            await self.query(TOOLCHAIN_INTEGRATION_URL, action='POST', payload=ti.to_dict())
        )

    async def edit(self, ti: ToolchainIntegration) -> ToolchainIntegration:
        """
        Edit Toolchain Integration

        :param ti: Toolchain Integration
        :return Message from EDI server
        """
        return ToolchainIntegration.from_dict(
            await self.query(TOOLCHAIN_INTEGRATION_URL, action='PUT', payload=ti.to_dict())
        )

    async def delete(self, name: str) -> str:
        """
        Delete Toolchain Integrations

        :param name: Name of a Toolchain Integration
        :return Message from EDI server
        """
        return await self.query(f'{TOOLCHAIN_INTEGRATION_URL}/{name}', action='DELETE')
