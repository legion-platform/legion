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
import typing

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

LEGION_CLOUD_CREDENTIALS_EDI = 'X-Legion-Cloud-Endpoint'
LEGION_CLOUD_CREDENTIALS_TOKEN = 'X-Legion-Cloud-Token'


# pylint: disable=W0223
class BaseCloudLegionHandler(BaseLegionHandler):
    """
    Base handler for cloud API
    """

    def build_cloud_client(self, target_client_class):
        """
        Build client for REST API

        :param target_client_class: target client's class
        :type target_client_class: type
        :return: [target_client_class] -- instance of target_client_class class
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

    def get_cloud_trainings(self) -> typing.List[dict]:
        """
        Get cloud trainings status

        :return: typing.List[dict] -- list of trainings
        """
        client: ModelTrainingClient = self.build_cloud_client(ModelTrainingClient)
        return [
            training.to_dict()
            for training in client.get_all()
        ]

    def get_cloud_deployments(self) -> typing.List[dict]:
        """
        Get cloud deployments status

        :return: typing.List[dict] -- list of deployments
        """
        client: ModelDeploymentClient = self.build_cloud_client(ModelDeploymentClient)
        return [
            deployment.to_dict()
            for deployment in client.get_all()
        ]

    def get_conn_instances(self) -> typing.List[dict]:
        """
        Get connections instances

        :return: typing.List[dict] -- list of connections
        """
        client: ConnectionClient = self.build_cloud_client(ConnectionClient)
        return [
            conn.to_dict()
            for conn in client.get_all()
        ]

    def get_model_packaging_instances(self) -> typing.List[dict]:
        """
        Get model packaging

        :return: typing.List[dict] -- list of model packaging
        """
        client: ModelPackagingClient = self.build_cloud_client(ModelPackagingClient)
        return [
            mp.to_dict()
            for mp in client.get_all()
        ]

    def get_packaging_integrations(self) -> typing.List[dict]:
        """
        Get packaging integrations

        :return: typing.List[dict] -- list of packaging integrations
        """
        client: PackagingIntegrationClient = self.build_cloud_client(PackagingIntegrationClient)
        return [
            pi.to_dict()
            for pi in client.get_all()
        ]

    def get_configuration(self) -> typing.Dict:
        """
        Get Legion configuration

        :return: Legion configuration
        """
        client: ConfigurationClient = self.build_cloud_client(ConfigurationClient)
        return client.get().to_dict()

    def get_toolchain_integrations(self) -> typing.List[dict]:
        """
        Get toolchain integrations

        :return: typing.List[dict] -- list of toolchain integrations
        """
        client: ToolchainIntegrationClient = self.build_cloud_client(ToolchainIntegrationClient)
        return [
            ti.to_dict()
            for ti in client.get_all()
        ]


class CloudModelPackagingHandler(BaseCloudLegionHandler):
    """
    Control model packagings
    """

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
        :type training_name: str
        :return: None
        """
        client = self.build_cloud_client(ModelTrainingClient)
        training = client.get(training_name)  # type: ModelTraining

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
        :type packaging_name: str
        :return: None
        """
        client = self.build_cloud_client(ModelPackagingClient)
        mp: ModelPackaging = client.get(packaging_name)

        self.finish_with_json({
            'futureLogsExpected': mp.status.state not in (TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE),
            'data': '\n'.join(client.log(packaging_name))
        })


class CloudDeploymentsHandler(BaseCloudLegionHandler):
    """
    Control cloud deployments
    """

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
    def _prepare_resources_list(resources: typing.Tuple[LegionCloudResourceUpdatePair]):
        """
        Prepare resources list to output

        :param resources: resources to output
        :type resources:  typing.Tuple[LegionCloudResourceUpdatePair]
        :return: typing.List[str] -- response
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


class CloudAllEntitiesHandler(BaseCloudLegionHandler):
    """
    Return all information for cloud mode
    """

    @decorate_handler_for_exception
    def get(self):
        """
        Get all information related to cloud state

        :return: None
        """
        self.finish_with_json({
            'trainings': self.get_cloud_trainings(),
            'deployments': self.get_cloud_deployments(),
            'connections': self.get_conn_instances(),
            'modelPackagings': self.get_model_packaging_instances(),
            'toolchainIntegrations': self.get_toolchain_integrations(),
            'packagingIntegrations': self.get_packaging_integrations(),
            'configuration': self.get_configuration()
        })
