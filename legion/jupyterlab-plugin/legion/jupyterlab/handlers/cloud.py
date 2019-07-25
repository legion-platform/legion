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
import functools
import typing

from tornado.web import HTTPError

from legion.sdk.clients.edi import EDIConnectionException, IncorrectAuthorizationToken, RemoteEdiClient
from legion.sdk.clients.edi_aggregated import parse_resources_file, apply, LegionCloudResourceUpdatePair
from legion.sdk.clients.training import ModelTrainingClient, ModelTraining, \
    TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE
from legion.sdk.clients.deployment import ModelDeploymentClient, ModelDeployment
from legion.sdk.clients.vcs import VcsClient, VCSCredential

from legion.jupyterlab.handlers.base import BaseLegionHandler
from legion.jupyterlab.handlers.datamodels.cloud import *  # pylint: disable=W0614, W0401

LEGION_CLOUD_CREDENTIALS_EDI = 'X-Legion-Cloud-Endpoint'
LEGION_CLOUD_CREDENTIALS_TOKEN = 'X-Legion-Cloud-Token'


def _decorate_handler_for_exception(function):
    """
    Wrap API handler to properly handle EDI client exceptions

    :param function: function to wrap
    :return: wrapped function
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except IncorrectAuthorizationToken as base_exception:
            raise HTTPError(log_message=str(base_exception), status_code=403) from base_exception
        except EDIConnectionException as base_exception:
            raise HTTPError(log_message=str(base_exception)) from base_exception
    return wrapper


# pylint: disable=W0223
class BaseCloudLegionHandler(BaseLegionHandler):
    """
    Base handler for cloud API
    """

    @staticmethod
    def transform_cloud_training(training: ModelTraining) -> dict:
        """
        Transform cloud training information object to dict

        :type training: ModelTraining
        :param training: cloud training information object
        :return: dict
        """
        return training.to_json(True)

    @staticmethod
    def transform_cloud_deployment(deployment: ModelDeployment) -> dict:
        """
        Transform cloud deployment object to dict

        :type deployment: ModelDeployment
        :param deployment: deployment object
        :return: dict
        """
        return deployment.to_json(True)

    @staticmethod
    def transform_vcs(vcs: VCSCredential) -> dict:
        """
        Transform VCS object to dict

        :type vcs: VCSCredential
        :param vcs: VCS object
        :return: dict
        """
        return vcs.to_json()

    def build_cloud_client(self, target_client_class):
        """
        Build client for REST API

        :param target_client_class: target client's class
        :type target_client_class: type
        :return: [target_client_class] -- instance of target_client_class class
        """
        edi_url = self.request.headers.get(LEGION_CLOUD_CREDENTIALS_EDI, '')
        edi_token = self.request.headers.get(LEGION_CLOUD_CREDENTIALS_TOKEN, '')

        if not edi_url:
            raise HTTPError(log_message='Credentials are corrupted')

        return target_client_class(edi_url, edi_token)

    def get_cloud_trainings(self) -> typing.List[dict]:
        """
        Get cloud trainings status

        :return: typing.List[dict] -- list of trainings
        """
        client = self.build_cloud_client(ModelTrainingClient)
        return [
            self.transform_cloud_training(training)
            for training in client.get_all()
        ]

    def get_cloud_deployments(self) -> typing.List[dict]:
        """
        Get cloud deployments status

        :return: typing.List[dict] -- list of deployments
        """
        client = self.build_cloud_client(ModelDeploymentClient)
        return [
            self.transform_cloud_deployment(deployment)
            for deployment in client.get_all()
        ]

    def get_vcs_instances(self) -> typing.List[dict]:
        """
        Get VCS instances

        :return: typing.List[dict] -- list of VCSs
        """
        client = self.build_cloud_client(VcsClient)
        return [
            self.transform_vcs(vcs)
            for vcs in client.get_all()
        ]


class CloudTrainingsHandler(BaseCloudLegionHandler):
    """
    Control cloud trainings
    """

    @_decorate_handler_for_exception
    def delete(self):
        """
        Remove cloud training

        :return: None
        """
        data = BasicNameRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelTrainingClient)
            client.delete(data.name)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model training') from query_exception


class CloudTrainingLogsHandler(BaseCloudLegionHandler):
    """
    Control cloud training logs
    """

    @_decorate_handler_for_exception
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
            'futureLogsExpected': training.state not in (TRAINING_SUCCESS_STATE, TRAINING_FAILED_STATE),
            'data': '\n'.join(client.log(training_name))
        })


class CloudDeploymentsHandler(BaseCloudLegionHandler):
    """
    Control cloud deployments
    """

    @_decorate_handler_for_exception
    def post(self):
        """
        Create new cloud deployment

        :return: None
        """
        data = DeploymentCreateRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelDeploymentClient)
            client.create(data.convert_to_deployment())
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not create new cloud deployment') from query_exception

    @_decorate_handler_for_exception
    def delete(self):
        """
        Remove local deployment

        :return: None
        """
        data = BasicNameRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(ModelDeploymentClient)
            client.delete(data.name)
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove cluster model deployment') from query_exception

        self.finish_with_json()


class CloudTokenIssueHandler(BaseCloudLegionHandler):
    """
    Control issuing new tokens
    """

    @_decorate_handler_for_exception
    def post(self):
        """
        Issue new token for model API

        :return: None
        """
        data = IssueTokenRequest(**self.get_json_body())

        try:
            client = self.build_cloud_client(RemoteEdiClient)
            token = client.get_token(data.role_name)
            self.finish_with_json({'token': token})
        except Exception as query_exception:
            raise HTTPError(log_message='Can not query cloud deployments') from query_exception


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
        return [f'{type(resource.resource).__name__} {resource.resource_name}' for resource in resources]

    @_decorate_handler_for_exception
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

    @_decorate_handler_for_exception
    def get(self):
        """
        Get all information related to cloud state

        :return: None
        """
        self.finish_with_json({
            'trainings': self.get_cloud_trainings(),
            'deployments': self.get_cloud_deployments(),
            'vcss': self.get_vcs_instances()
        })
