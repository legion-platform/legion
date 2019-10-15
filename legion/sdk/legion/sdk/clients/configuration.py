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

from legion.sdk.clients.edi import RemoteEdiClient, AsyncRemoteEdiClient
from legion.sdk.definitions import CONFIGURATION_URL
from legion.sdk.models import Configuration

LOGGER = logging.getLogger(__name__)


class ConfigurationClient(RemoteEdiClient):
    """
    HTTP connection client
    """

    def get(self) -> Configuration:
        """
        Get Configuration from EDI server

        :return: Configuration
        """
        return Configuration.from_dict(self.query(CONFIGURATION_URL))

    def edit(self, conf: Configuration) -> Configuration:
        """
        Edit Configuration

        :param conf: Configuration
        :return Message from EDI server
        """
        return Configuration.from_dict(self.query(CONFIGURATION_URL, action='PUT', payload=conf.to_dict()))


class AsyncConfigurationClient(AsyncRemoteEdiClient):
    """
    HTTP connection async client
    """

    async def get(self) -> Configuration:
        """
        Get Configuration from EDI server

        :return: Configuration
        """
        return Configuration.from_dict(await self.query(CONFIGURATION_URL))

    async def edit(self, conf: Configuration) -> Configuration:
        """
        Edit Configuration

        :param conf: Configuration
        :return Message from EDI server
        """
        return Configuration.from_dict(await self.query(CONFIGURATION_URL, action='PUT', payload=conf.to_dict()))
