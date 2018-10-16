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

import json
import logging
import os

import legion.k8s
import legion.edi.server
import legion.config
import requests
import requests.exceptions

LOGGER = logging.getLogger(__name__)


class EdiClient:
    """
    EDI client
    """

    def __init__(self, base=None, token=None, retries=3, http_client=None, use_relative_url=False):
        """
        Build client

        :param base: base url, for example: http://edi.parallels
        :type base: str
        :param token: token for token based auth
        :type token: str or None
        :param retries: command retries or less then 2 if disabled
        :type retries: int
        :param http_client: HTTP client (default: requests)
        :type http_client: python class that implements requests-like post & get methods
        :param use_relative_url: use non-full get/post requests (useful for testings)
        :type use_relative_url: bool
        """
        self._base = base
        self._token = token
        self._version = legion.edi.server.EDI_VERSION
        self._retries = retries
        if http_client:
            self._http_client = http_client
        else:
            self._http_client = requests
        self._use_relative_url = use_relative_url

    def _query(self, endpoint_declaration, payload=None, url_substitutes=None):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :type url_template: str
        :param payload: data payload or None
        :type payload: dict[str, any]
        :param url_substitutes: data for replacing URL
        :type url_substitutes: dict[str, str]
        :return: dict[str, any] -- response content
        """
        url_template = endpoint_declaration[0]
        http_method = endpoint_declaration[1].lower()

        url_substitutes_dict = {'version': self._version}
        if url_substitutes:
            url_substitutes_dict.update(url_substitutes)

        sub_url = url_template.format(**url_substitutes_dict)
        if self._use_relative_url:
            target_url = sub_url
        else:
            target_url = self._base.strip('/') + sub_url

        headers = {}

        left_retries = self._retries if self._retries > 0 else 1
        raised_exception = None

        while left_retries > 0:
            try:
                LOGGER.debug('Requesting {} in {} mode'.format(target_url, http_method))
                if hasattr(self._http_client, 'request'):
                    response = self._http_client.request(http_method, target_url, data=payload, headers=headers)
                else:
                    response = self._http_client.open(target_url, method=http_method, data=payload, headers=headers)
            except requests.exceptions.ConnectionError as exception:
                LOGGER.error('Failed to connect to {}: {}. Retrying'.format(self._base, exception))
                raised_exception = exception
            else:
                LOGGER.debug('Got response. Breaking')
                break

            left_retries -= 1
        else:
            raise Exception('Failed to connect to {}. No one retry left. Exception: {}'.format(
                self._base, raised_exception
            ))

        if hasattr(response, 'text'):
            response_data = response.text
        else:
            response_data = response.data

        if isinstance(response_data, bytes):
            response_data = response_data.decode('utf-8')

        try:
            answer = json.loads(response_data)
            LOGGER.debug('Got answer: {!r} with code {} for URL {!r}'
                         .format(answer, response.status_code, target_url))
        except ValueError as json_decode_exception:
            raise ValueError('Invalid JSON structure {!r}: {}'.format(response_data, json_decode_exception))

        if isinstance(answer, dict) and answer.get('error', False):
            exception = answer.get('exception')
            raise Exception('Got error from server: {!r}'.format(exception))

        if response.status_code != 200:
            raise Exception('Server returned wrong HTTP code (not 200) without error flag')

        LOGGER.debug('Query has been completed, parsed and validated')
        return answer

    @staticmethod
    def parse_deployments(response):
        """
        Parse model deployments from response

        :param response: EDI server response
        :type response: list[dict[str, any]]
        :return: list[:py:class:`legion.k8s.ModelDeploymentDescription`] -- parsed model deployments
        """
        return [legion.k8s.ModelDeploymentDescription.build_from_json(x) for x in response]

    def inspect(self, model=None, version=None):
        """
        Perform inspect query on EDI server

        :param model: model id
        :type model: str
        :param version: (Optional) model version
        :type version: str
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
        """
        payload = {}
        if model:
            payload['model'] = model
        if version:
            payload['version'] = version

        return self.parse_deployments(self._query(legion.edi.server.EDI_INSPECT, payload=payload))

    def info(self):
        """
        Perform info query on EDI server

        :return: dict[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
        """
        return self._query(legion.edi.server.EDI_INFO)

    def deploy(self, image, count=1, livenesstimeout=2, readinesstimeout=2):
        """
        Deploy API endpoint

        :param image: Docker image for deploy (for kubernetes deployment and local pull)
        :type image: str
        :param count: count of pods to create
        :type count: int
        :param livenesstimeout: model pod startup timeout (used in liveness probe)
        :type livenesstimeout: int
        :param readinesstimeout: model pod startup timeout (used readiness probe)
        :type readinesstimeout: int
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        payload = {
            'image': image
        }
        if count is not None:
            payload['count'] = count
        if livenesstimeout:
            payload['livenesstimeout'] = livenesstimeout
        if readinesstimeout:
            payload['readinesstimeout'] = readinesstimeout

        return self.parse_deployments(self._query(legion.edi.server.EDI_DEPLOY, payload=payload))

    def undeploy(self, model, grace_period=0, version=None, ignore_not_found=False):
        """
        Undeploy API endpoint

        :param model: model id
        :type model: str
        :param grace_period: grace period for removing
        :type grace_period: int
        :param version: (Optional) model version
        :type version: str
        :param ignore_not_found: (Optional) ignore if cannot find models
        :type ignore_not_found: bool
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        payload = {
            'model': model,
            'ignore_not_found': ignore_not_found
        }

        if grace_period:
            payload['grace_period'] = grace_period

        if version:
            payload['version'] = version

        return self.parse_deployments(self._query(legion.edi.server.EDI_UNDEPLOY, payload=payload))

    def scale(self, model, count, version=None):
        """
        Scale model

        :param model: model id
        :type model: str
        :param count: count of pods to create
        :type count: int
        :param version: (Optional) model version
        :type version: str
        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- affected model deployments
        """
        payload = {
            'model': model,
            'count': count
        }
        if version:
            payload['version'] = version

        return self.parse_deployments(self._query(legion.edi.server.EDI_SCALE, payload=payload))

    def get_token(self, version=None):
        """
        Get API token

        :param version: (Optional) model version
        :type version: str
        :return: str -- return API Token
        """
        payload = {}
        if version:
            payload['version'] = version

        response = self._query(legion.edi.server.EDI_GENERATE_TOKEN, payload=payload)
        if response and 'token' in response:
            return response['token']

    def train_ml_import(self, project_name, vcs_project_url, vcs_credentials=None, ci_pipeline_path=None):
        """
        Import project

        :param project_name: name of project
        :type project_name: str
        :param vcs_project_url: project URL in VCS (git / svn and so on). E.g. ssh://git@.../project_name or https://...
        :type vcs_project_url: str
        :param vcs_credentials: (Optional) credentials for connection to VCS
        :type vcs_credentials: str
        :param ci_pipeline_path: (Optional) custom path to pipeline declaration inside VCS
        :type ci_pipeline_path: str
        :return:
        """
        payload = {
            'project_name': project_name,
            'vcs_project_url': vcs_project_url
        }
        if vcs_credentials:
            payload['vcs_credentials'] = vcs_credentials
        if vcs_credentials:
            payload['ci_pipeline_path'] = ci_pipeline_path

        return self._query(legion.edi.server.EDI_TRAIN_ML_IMPORT,
                           payload=payload)

    def train_ml_remove(self, project_name):
        """
        Remove project

        :param project_name: name of project
        :type project_name: str
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_REMOVE,
                           url_substitutes={'project_name': project_name})

    def train_ml_execute(self, project_name, profile_name=None):
        """
        Execute project. It creates new execution

        :param project_name: name of project
        :type project_name: str
        :param profile_name: (Optional) name of profile
        :type profile_name: str or None
        :return:
        """
        payload = {}
        if profile_name:
            payload['profile_name'] = profile_name

        return self._query(legion.edi.server.EDI_TRAIN_ML_EXECUTE,
                           payload=payload,
                           url_substitutes={'project_name': project_name})

    def train_ml_history(self, project_name):
        """
        Get list of existed executions

        :param project_name: name of project
        :type project_name: str
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_HISTORY,
                           url_substitutes={'project_name': project_name})

    def train_ml_cancel(self, project_name, execution_id):
        """
        Cancel execution

        :param project_name: name of project
        :type project_name: str
        :param execution_id: id of execution
        :type execution_id: int
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_CANCEL,
                           url_substitutes={'project_name': project_name, 'execution_id': execution_id})

    def train_ml_status(self, project_name, execution_id):
        """
        Get status of execution

        :param project_name: name of project
        :type project_name: str
        :param execution_id: id of execution
        :type execution_id: int
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_STATUS,
                           url_substitutes={'project_name': project_name, 'execution_id': execution_id})

    def train_ml_logs(self, project_name, execution_id):
        """
        Get execution logs

        :param project_name: name of project
        :type project_name: str
        :param execution_id: id of execution
        :type execution_id: int
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_LOGS,
                           url_substitutes={'project_name': project_name, 'execution_id': execution_id})

    def train_ml_inspect(self):
        """
        Get list of executions

        :param project_name: name of project
        :type project_name: str
        :return:
        """
        return self._query(legion.edi.server.EDI_TRAIN_ML_INSPECT)

    def __repr__(self):
        """
        Get string representation of object

        :return: str -- string representation
        """
        return "EdiClient({!r})".format(self._base)

    __str__ = __repr__


def add_edi_arguments(parser):
    """
    Add EDI arguments parser

    :param parser:
    :type parser:
    :return:
    """
    parser.add_argument('--edi',
                        type=str, help='EDI server host')
    parser.add_argument('--user',
                        type=str, help='EDI server user')
    parser.add_argument('--password',
                        type=str, help='EDI server password')
    parser.add_argument('--token',
                        type=str, help='EDI server token')


def build_client(args=None):
    """
    Build EDI client from from ENV and from command line arguments

    :param args: (optional) command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`legion.external.edi.EdiClient` -- EDI client
    """
    host, user, password, token = None, None, None, None

    if args:
        if args.edi:
            host = args.edi

        if args.user:
            user = args.user

        if args.password:
            password = args.password

        if args.token:
            token = args.token

    if not host:
        try:
            host = legion.k8s.Enclave(os.environ.get("NAMESPACE")).edi_service.url
        except Exception:
            host = os.environ.get(*legion.config.EDI_URL)

    if not user or not password:
        user = os.environ.get(*legion.config.EDI_USER)
        password = os.environ.get(*legion.config.EDI_PASSWORD)

    if not token:
        token = os.environ.get(*legion.config.EDI_TOKEN)

    client = EdiClient(host, user, password, token)
    return client
