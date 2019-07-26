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
from legion.sdk.definitions import MODEL_ROUTE_URL
from legion.sdk.models import ModelRoute

LOGGER = logging.getLogger(__name__)

READY_STATE = "Ready"
PROCESSING_STATE = "Processing"


class ModelRouteClient(RemoteEdiClient):
    """
    HTTP model route client
    """

    def get(self, name: str) -> ModelRoute:
        """
        Get Model Route from EDI server

        :param name: Model Route name
        :type name: str
        :return: Model Route
        """
        return ModelRoute.from_dict(self.query(f'{MODEL_ROUTE_URL}/{name}'))

    def get_all(self) -> typing.List[ModelRoute]:
        """
        Get all Model Routes from EDI server

        :return: all Model Routes
        """
        return [ModelRoute.from_dict(mr) for mr in self.query(MODEL_ROUTE_URL)]

    def create(self, mr: ModelRoute) -> ModelRoute:
        """
        Create Model Route

        :param mr: Model Route
        :return Message from EDI server
        """
        return ModelRoute.from_dict(
            self.query(MODEL_ROUTE_URL, action='POST', payload=mr.to_dict())
        )

    def edit(self, mr: ModelRoute) -> ModelRoute:
        """
        Edit Model Route

        :param mr: Model Route
        :return Message from EDI server
        """
        return ModelRoute.from_dict(
            self.query(MODEL_ROUTE_URL, action='PUT', payload=mr.to_dict())
        )

    def delete(self, name: str) -> str:
        """
        Delete Model Routes

        :param name: Name of a Model Route
        :return Message from EDI server
        """
        return self.query(f'{MODEL_ROUTE_URL}/{name}', action='DELETE')
