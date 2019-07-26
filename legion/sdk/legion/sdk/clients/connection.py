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

from legion.sdk.clients.edi import RemoteEdiClient
from legion.sdk.definitions import CONNECTION_URL
from legion.sdk.models import Connection

LOGGER = logging.getLogger(__name__)


class ConnectionClient(RemoteEdiClient):
    """
    HTTP connection client
    """

    def get(self, name: str) -> Connection:
        """
        Get Connection from EDI server

        :param name: Connection name
        :type name: str
        :return: Connection
        """
        return Connection.from_dict(self.query(f'{CONNECTION_URL}/{name}'))

    def get_all(self) -> typing.List[Connection]:
        """
        Get all Connections from EDI server

        :return: all Connections
        """
        return [Connection.from_dict(conn) for conn in self.query(CONNECTION_URL)]

    def create(self, conn: Connection) -> Connection:
        """
        Create Connection

        :param conn: Connection
        :return Message from EDI server
        """
        return Connection.from_dict(self.query(CONNECTION_URL, action='POST', payload=conn.to_dict()))

    def edit(self, conn: Connection) -> Connection:
        """
        Edit Connection

        :param conn: Connection
        :return Message from EDI server
        """
        return Connection.from_dict(self.query(CONNECTION_URL, action='PUT', payload=conn.to_dict()))

    def delete(self, name: str) -> str:
        """
        Delete Connections

        :param name: Name of a Connection
        :return Message from EDI server
        """
        return self.query(f'{CONNECTION_URL}/{name}', action='DELETE')['message']
