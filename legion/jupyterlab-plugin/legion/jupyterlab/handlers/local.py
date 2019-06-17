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
Declaration of local handlers
"""
import datetime
import os
import multiprocessing
import subprocess

from tornado.web import HTTPError

from legion.sdk.clients.edi import LocalEdiClient
from legion.sdk.containers.definitions import ModelDeploymentDescription, ModelBuildInformation

from legion.jupyterlab.handlers.base import BaseLegionHandler
from legion.jupyterlab.handlers.datamodels.local import *  # pylint: disable=W0614, W0401


BUILD_LOCK = multiprocessing.Lock()


# pylint: disable=W0223, W0201
class BaseLocalLegionHandler(BaseLegionHandler):
    """
    Base handler for local mode of Legion plugin
    """

    def initialize(self, state, logger, **kwargs):
        """
        Initialize base handler

        :param state: state of plugin back-end
        :param logger: logger to log data to
        :param kwargs: additional arguments
        :return: None
        """
        super().initialize(state, logger, **kwargs)
        self.client = LocalEdiClient()

    @staticmethod
    def transform_local_build(build: ModelBuildInformation) -> dict:
        """
        Transform build information object to dict

        :type build: ModelBuildInformation
        :param build: build information object
        :return: dict
        """
        return {
            'imageName': build.image_name,
            'modelName': build.model_id,
            'modelVersion': build.model_version
        }

    @staticmethod
    def transform_local_deployment(deployment: ModelDeploymentDescription) -> dict:
        """
        Transform local deployment object to dict

        :type deployment: ModelDeploymentDescription
        :param deployment: deployment object
        :return: dict
        """
        return {
            'name': deployment.deployment_name,
            'image': deployment.image,
            'port': deployment.local_port
        }

    def get_local_builds(self):
        """
        Get local builds status

        :return: typing.List[dict] -- list of builds
        """
        return [
            self.transform_local_build(build)
            for build in self.client.get_builds()
        ]

    def get_local_deployments(self):
        """
        Get local deployments status

        :return: typing.List[dict] -- list of deployments
        """
        return [
            self.transform_local_deployment(deployment)
            for deployment in self.client.inspect()
        ]

    def start_build(self) -> None:
        """
        Start new build

        :return: None
        """
        with BUILD_LOCK:
            self.logger.debug('Trying to start building of local container')
            process = self.state.local_build_process  # type: typing.Optional[subprocess.Popen]

            if process and process.poll() is None:
                self.logger.warning('Building process already alive. Ignoring...')
                return

            self.logger.info('Starting self-build process with logging to %s', self.state.local_build_storage)
            command = ['legionctl', '--verbose', 'build']

            # Opening output stream, writing intro-line
            output_stream = open(self.state.local_build_storage, 'w')
            print('{} Starting command {!r} in working directory {!r}'.format(
                datetime.datetime.now(), command, os.getcwd()
            ), file=output_stream, flush=True)

            # Starting process
            new_process = subprocess.Popen(command,
                                           stdout=output_stream, stderr=subprocess.STDOUT)
            self.state.register_local_build(new_process)

    def _get_local_build_logs(self) -> str:
        """
        Get logs of local build process

        return: str -- logs
        """
        try:
            with open(self.state.local_build_storage, 'r') as log_stream:
                return log_stream.read()
        except Exception as log_stream_exception:
            self.logger.exception(log_stream_exception)
            return ''

    def get_build_status(self) -> dict:
        """
        Get status of build process

        :return: dict -- build status
        """
        with BUILD_LOCK:
            self.logger.error(f"ST: {self.state!r}")
            process = self.state.local_build_process  # type: typing.Optional[subprocess.Popen]

            is_alive = process is not None and process.poll() is None

        if process:
            return {
                'started': True,
                'finished': not is_alive,
                'logs': self._get_local_build_logs()
            }
        else:
            return {
                'started': False,
                'finished': False,
                'logs': self._get_local_build_logs()
            }


class LocalBuildsHandler(BaseLocalLegionHandler):
    """
    Control local builds (it can show information about current build and start a new one)
    """

    def get(self):
        """
        Get local builds information

        :return: None
        """
        try:
            self.finish_with_json(self.get_local_builds())
        except Exception as query_exception:
            raise HTTPError(log_message='Can not query local builds') from query_exception

    def post(self):
        """
        Start local build

        :return: None
        """
        self.start_build()
        self.finish_with_json()


class LocalDeploymentsHandler(BaseLocalLegionHandler):
    """
    Control all local deployments
    """

    def get(self):
        """
        Get information about local deployments

        :return: None
        """
        try:
            self.finish_with_json(self.get_local_deployments())
        except Exception as query_exception:
            raise HTTPError(log_message='Can not query local deployments') from query_exception

    def post(self):
        """
        Deploy new model locally

        :return: None
        """
        data = DeployCreateRequest(**self.get_json_body())

        try:
            deployments = self.client.deploy(data.name, data.image, data.port)
        except Exception as query_exception:
            raise HTTPError(log_message='Can not deploy model locally') from query_exception

        if deployments:
            return self.finish_with_json(self.transform_local_deployment(deployments[0]))
        else:
            raise HTTPError(log_message='Back-end did not return information about created deployment')

    def delete(self):
        """
        Remove local deployment

        :return: None
        """
        data = BasicNameRequest(**self.get_json_body())

        try:
            self.client.undeploy(data.name)
            self.finish_with_json()
        except Exception as query_exception:
            raise HTTPError(log_message='Can not remove local model deployment') from query_exception


class LocalBuildStatusHandler(BaseLocalLegionHandler):
    """
    Return information about local build
    """

    def get(self):
        """
        Get information about local build status

        :return: None
        """
        self.finish_with_json(self.get_build_status())


class LocalMetricsHandler(BaseLocalLegionHandler):
    """
    Return information about local metrics
    """

    def get(self):
        """
        Get local metrics

        :return: None
        """
        try:
            import legion.toolchain.metrics
        except ModuleNotFoundError as import_error:
            self.logger.exception(import_error)
            raise HTTPError(log_message='Legion Toolchain is not installed')

        metrics = legion.toolchain.metrics.show_local_metrics()

        self.finish(metrics.to_json(orient='split'))


class LocalAllEntitiesHandler(BaseLocalLegionHandler):
    """
    Return all information for local mode
    """

    def get(self):
        """
        Get all information related to local mode state

        :return: None
        """
        self.finish_with_json({
            'builds': self.get_local_builds(),
            'deployments': self.get_local_deployments(),
            'buildStatus': self.get_build_status()
        })
