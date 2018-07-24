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
Graphana API functional for working with models
"""

import json
import os

import legion.config
from legion.utils import render_template

import requests


class GrafanaClient:
    """
    Base Grafana HTTP API client
    """

    def __init__(self, base, user=None, password=None):
        """
        Build client

        :param base: base url, for example: http://parallels/grafana/
        :type base: str
        :param user: user name
        :type user: str or None
        :param password: user password
        :type password: str or None
        """
        self._base = base.strip('/')
        self._user = user
        self._password = password

    def _query(self, url, payload=None, action='GET'):
        """
        Perform query to Grafana server

        :param url: query suburl, for example: /api/search/
        :type url: str
        :param payload: payload (will be converted to JSON) or None
        :type payload: dict[str, any]
        :param action: HTTP method (GET, POST, PUT, DELETE)
        :type action: str
        :return: dict[str, any] -- response content
        """
        full_url = self._base + url

        headers = {
            'Content-Type': 'application/json'
        }

        auth = None
        if self._user and self._password:
            auth = (self._user, self._password)

        response = requests.request(action.lower(), full_url, json=payload, headers=headers, auth=auth)

        if response.status_code in (401, 403):
            raise Exception('Auth failed')

        if response.status_code != 200:
            raise Exception('Wrong answer for url = %s: %s' % (full_url, repr(response)))

        answer = json.loads(response.text)

        return answer

    def delete_dashboard(self, dashboard_uri):
        """
        Delete dashboard by url

        :param dashboard_uri: dashboard uri
        :type dashboard_uri: str
        :return: None
        """
        self._query('/api/dashboards/%s' % dashboard_uri, action='DELETE')

    def remove_dashboard_for_model(self, model_id, model_version):
        """
        Remove model's dashboard

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_id: str or None
        :return: None
        """
        if self.is_dashboard_exists(model_id, model_version):
            dashboard = self.get_model_dashboard(model_id, model_version)
            self.delete_dashboard(dashboard['uri'])

    def is_dashboard_exists(self, model_id, model_version):
        """
        Check if model's dashboard exists

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_id: str or None
        :return: bool -- is dashboard exists
        """
        return self.get_model_dashboard(model_id, model_version) is not None

    def get_model_dashboard(self, model_id, model_version):
        """
        Search for model's dashboard

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_id: str or None
        :return: dict with dashboard information or None
        """
        data = self._query('/api/search/?tag=model_{}'.format(model_id))
        if not data:
            return None

        return data[0]

    def create_dashboard_for_model(self, model_id, model_version=None):
        """
        Create model's dashboard from template

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_id: str or None
        :return: None
        """
        self.remove_dashboard_for_model(model_id, model_version)

        json_string = render_template('grafana-dashboard.json.tmpl', {
            'MODEL_ID': model_id,
            'MODEL_VERSION': model_version
        })

        dashboard = json.loads(json_string)

        payload = {
            'overwrite': False,
            'dashboard': dashboard
        }
        self._query('/api/dashboards/db', payload, 'POST')


def build_client(args):
    """
    Build Grafana client from ENV and from command line arguments

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`legion.grafana.GrafanaClient`
    """
    host = os.environ.get(*legion.config.GRAFANA_URL)
    user = os.environ.get(*legion.config.GRAFANA_USER)
    password = os.environ.get(*legion.config.GRAFANA_PASSWORD)

    if args.grafana_server:
        host = args.grafana_server

    if args.grafana_user:
        user = args.grafana_user

    if args.grafana_password:
        password = args.grafana_password

    client = GrafanaClient(host, user, password)

    return client
