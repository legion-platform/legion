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

    def __init__(self, base, user=None, password=None, token=None):
        """
        Build client

        :param base: base url, for example: http://edi.parallels
        :type base: str
        :param user: user name for user/password based auth
        :type user: str or None
        :param password: user password for user/password based auth
        :type password: str or None
        :param token: token for token based auth
        :type token: str or None
        """
        self._base = base
        self._user = user
        self._password = password
        self._token = token
        self._version = legion.edi.server.EDI_VERSION

    def _query(self, url_template, payload=None, action='GET'):
        """
        Perform query to EDI server

        :param url_template: url template from legion.const.api
        :type url_template: str
        :param payload: payload (will be converted to JSON) or None
        :type payload: dict[str, any]
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :type action: str
        :return: dict[str, any] -- response content
        """
        sub_url = url_template.format(version=self._version)
        full_url = self._base.strip('/') + sub_url

        auth = None
        headers = {}

        if self._user and self._password:
            auth = (self._user, self._password)
        elif self._token:
            auth = ('token', self._token)

        try:
            response = requests.request(action.lower(), full_url, data=payload, headers=headers, auth=auth)
        except requests.exceptions.ConnectionError as exception:
            raise Exception('Cannot connect to EDI server: %s. Exception: %s' % (self._base, exception))

        if response.status_code in (401, 403):
            raise Exception('Auth failed')
        try:
            answer = json.loads(response.text)
        except ValueError as json_decode_exception:
            raise Exception('Cannot parse answer: %s. HTTP CODE: %d. Exception: %s'
                            % (response.text, response.status_code, json_decode_exception))

        if 'error' in answer and answer['error']:
            print(repr(answer))
            raise Exception('Server returns error: %s' % answer.get('message', 'UNKNOWN'))

        if response.status_code != 200:
            raise Exception('Wrong HTTP code (%d) for url = %s: %s. %s'
                            % (response.status_code, full_url, repr(response), response.text))

        return answer

    def inspect(self):
        """
        Perform inspect query on EDI server

        :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
        """
        answer = self._query(legion.edi.server.EDI_INSPECT)
        return [legion.k8s.ModelDeploymentDescription(**x) for x in answer]

    def info(self):
        """
        Perform info query on EDI server

        :return: dict[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
        """
        return self._query(legion.edi.server.EDI_INFO)

    def deploy(self, image, count=1, k8s_image=None):
        """
        Deploy API endpoint

        :param image: Docker image for deploy (for jybernetes deployment and local pull)
        :type image: str
        :param count: count of pods to create
        :type count: int
        :param k8s_image: Docker image for kubernetes deployment
        :type k8s_image: str or None
        :return: bool -- True
        """
        payload = {
            'image': image
        }
        if count:
            payload['count'] = count
        if k8s_image:
            payload['k8s_image'] = k8s_image

        return self._query(legion.edi.server.EDI_DEPLOY, action='POST', payload=payload)['status']

    def undeploy(self, model, grace_period=0, version=None):
        """
        Undeploy API endpoint

        :param model: model id
        :type model: str
        :param grace_period: grace period for removing
        :type grace_period: int
        :param version: (Optional) model version
        :type version: str
        :return: bool -- True
        """
        payload = {
            'model': model
        }

        if grace_period:
            payload['grace_period'] = grace_period

        if version:
            payload['version'] = version

        return self._query(legion.edi.server.EDI_UNDEPLOY, action='POST', payload=payload)['status']

    def scale(self, model, count, version=None):
        """
        Scale model

        :param model: model id
        :type model: str
        :param count: count of pods to create
        :type count: int
        :param version: (Optional) model version
        :type version: str
        :return: bool -- True
        """
        payload = {
            'model': model,
            'count': count
        }
        if version:
            payload['version'] = version

        return self._query(legion.edi.server.EDI_SCALE, action='POST', payload=payload)['status']


def build_client(args):
    """
    Build EDI client from from ENV and from command line arguments

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return:
    """
    host = os.environ.get(*legion.config.EDI_URL)
    user = os.environ.get(*legion.config.EDI_USER)
    password = os.environ.get(*legion.config.EDI_PASSWORD)
    token = os.environ.get(*legion.config.EDI_TOKEN)

    if args.edi:
        host = args.edi

    if args.user:
        user = args.user

    if args.password:
        password = args.password

    if args.token:
        token = args.token

    client = EdiClient(host, user, password, token)
    return client
