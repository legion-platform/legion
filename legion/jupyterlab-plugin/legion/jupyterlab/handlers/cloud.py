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
Declaration of cloud handlers
"""
import os
from typing import List, Dict, Tuple

from tornado.web import HTTPError

from legion.jupyterlab.handlers.base import BaseLegionHandler
from legion.jupyterlab.handlers.datamodels.cloud import *  # pylint: disable=W0614, W0401
from legion.jupyterlab.handlers.helper import decorate_handler_for_exception, DEFAULT_EDI_ENDPOINT, LEGION_X_JWT_TOKEN
from legion.sdk.clients.configuration import ConfigurationClient
from legion.sdk.clients.connection import ConnectionClient
from legion.sdk.clients.deployment import ModelDeploymentClient, ModelDeployment
from legion.sdk.clients.edi import EDIConnectionException, RemoteEdiClient
from legion.sdk.clients.edi_aggregated import parse_resources_file, apply, LegionCloudResourceUpdatePair
from legion.sdk.clients.packaging import ModelPackagingClient
from legion.sdk.clients.packaging_integration import PackagingIntegrationClient
from legion.sdk.clients.toolchain_integration import ToolchainIntegrationClient
from legion.sdk.clients.training import ModelTrainingClient, ModelTraining, \
    TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE
from legion.sdk.models import ModelPackaging
from legion.sdk.models.base_model_ import Model

LEGION_CLOUD_CREDENTIALS_EDI = 'X-Legion-Cloud-Endpoint'
LEGION_CLOUD_CREDENTIALS_TOKEN = 'X-Legion-Cloud-Token'


def _convert_to_dict(entities: List[Model]) -> List[Dict]:
    """
    Convert all Legion entities to the dict
    :param entities: Legion entities
    :return: list with converted Legion entities
    """
    return [ent.to_dict() for ent in entities]


# pylint: disable=W0223
class BaseCloudLegionHandler(BaseLegionHandler):
    """
    Base handler for cloud API
    """

    def build_cloud_client(self, target_client_class):
        """
        Build client for REST API

        :param target_client_class: target client's class
        :return: instance of target_client_class class
        """
        default_edi_url = os.getenv(DEFAULT_EDI_ENDPOINT, '')
        jwt_header = self.request.headers.get(LEGION_X_JWT_TOKEN, '')

        edi_url = self.request.headers.get(LEGION_CLOUD_CREDENTIALS_EDI, '')
        if not edi_url:
            edi_url = default_edi_url

        edi_token = self.request.headers.get(LEGION_CLOUD_CREDENTIALS_TOKEN, '')
        if jwt_header:
            edi_token = jwt_header

        if not edi_url:
            raise HTTPError(log_message='Credentials are corrupted')

        return target_client_class(edi_url, edi_token)


class CloudModelPackagingHandler(BaseCloudLegionHandler):
    """
    Control model packagings
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all model packagings

        :return: None
        """
        client: ModelPackagingClient = self.build_cloud_client(ModelPackagingClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))

    @decorate_handler_for_exception
    def delete(self):
        """
        Remove model packaging

        :return: None
        """
        data = BasicIdRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelPackagingClient)
            client.delete(data.id)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model packaging') from query_exception


class CloudUrlInfo(BaseCloudLegionHandler):
    """
    Control model packagings
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Remove model packaging

        :return: None
        """
        self.finish_with_json({
            'ediUrl': os.getenv('LEGION_EDI_URL', ''),
            'metricUiUrl': os.getenv('LEGION_METRIC_UI_URL', ''),
        })


class CloudTrainingsHandler(BaseCloudLegionHandler):
    """
    Control cloud trainings
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all trainings

        :return: None
        """
        client: ModelTrainingClient = self.build_cloud_client(ModelTrainingClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))

    @decorate_handler_for_exception
    def delete(self):
        """
        Remove cloud training

        :return: None
        """
        data = BasicIdRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelTrainingClient)
            client.delete(data.id)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model training') from query_exception


class CloudConnectionHandler(BaseCloudLegionHandler):
    """
    Control cloud connections
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all connections

        :return: None
        """
        client: ConnectionClient = self.build_cloud_client(ConnectionClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))

    @decorate_handler_for_exception
    def delete(self):
        """
        Remove cloud training

        :return: None
        """
        data = BasicIdRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ConnectionClient)
            client.delete(data.id)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model training') from query_exception


class CloudTrainingLogsHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @decorate_handler_for_exception
    def get(self, training_name):
        """
        Get training logs

        :arg training_name: name of training
        :return: None
        """
        client = self.build_cloud_client(ModelTrainingClient)
        training: ModelTraining = client.get(training_name)

        self.finish_with_json({
            'futureLogsExpected': training.status.state not in (TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE),
            'data': '\n'.join(client.log(training_name))
        })


class CloudPackagingLogsHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @decorate_handler_for_exception
    def get(self, packaging_name):
        """
        Get training logs

        :arg packaging_name: name of training
        :return: None
        """
        client = self.build_cloud_client(ModelPackagingClient)
        mp: ModelPackaging = client.get(packaging_name)

        self.finish_with_json({
            'futureLogsExpected': mp.status.state not in (TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE),
            'data': '\n'.join(client.log(packaging_name))
        })


class CloudPackagingIntegrationsHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all packaging integrations

        :return: None
        """
        client: PackagingIntegrationClient = self.build_cloud_client(PackagingIntegrationClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))


class CloudToolchainIntegrationsHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all toolchain intergrations

        :return: None
        """
        client: ToolchainIntegrationClient = self.build_cloud_client(ToolchainIntegrationClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))


class CloudConfiguratioHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get legio configuration

        :return: None
        """
        client: ConfigurationClient = self.build_cloud_client(ConfigurationClient)

        self.finish_with_json(client.get().to_dict())


class CloudDeploymentsHandler(BaseCloudLegionHandler):
    """
    Control cloud deployments
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all packaging integrations

        :return: None
        """
        client: ModelDeploymentClient = self.build_cloud_client(ModelDeploymentClient)

        self.finish_with_json(_convert_to_dict(client.get_all()))

    @decorate_handler_for_exception
    def post(self):
        """
        Create new cloud deployment

        :return: None
        """
        md = ModelDeployment.from_dict(self.get_json_body())

        try:
            client = self.build_cloud_client(ModelDeploymentClient)
            client.create(md)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not create new cloud deployment') from query_exception

    @decorate_handler_for_exception
    def delete(self):
        """
        Remove local deployment

        :return: None
        """
        data = BasicIdRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelDeploymentClient)
            client.delete(data.id)
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model deployment') from query_exception

        self.finish_with_json()


class CloudApplyFromFileHandler(BaseCloudLegionHandler):
    """
    Apply (create/update/delete) entities from file
    """

    @staticmethod
    def _prepare_resources_list(resources: Tuple[LegionCloudResourceUpdatePair]) -> List[str]:
        """
        Prepare resources list to output

        :param resources: resources to output
        :return: response
        """
        return [f'{type(resource.resource).__name__} {resource.resource_id}' for resource in resources]

    @decorate_handler_for_exception
    def post(self):
        """
        Apply entities from JSON/YAML file

        :return: None
        """
        data = ApplyFromFileRequest(**self.get_json_body())
        client = self.build_cloud_client(RemoteEdiClient)

        try:
            resources = parse_resources_file(data.path)
        except Exception as parse_exception:
            raise HTTPError(log_message=f'Can not parse resources file {data.path}: {parse_exception}')

        try:
            result = apply(resources, client, data.removal)
        except EDIConnectionException as edi_exception:
            raise edi_exception
        except Exception as apply_exception:
            raise HTTPError(log_message=f'Can not apply changes from resources file {data.path}: {apply_exception}')

        self.finish_with_json({
            'created': self._prepare_resources_list(result.created),
            'changed': self._prepare_resources_list(result.changed),
            'removed': self._prepare_resources_list(result.removed),
            'errors': [str(err) for err in result.errors],
        })
