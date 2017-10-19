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

from drun.external.base_grafana_client import BaseGrafanaClient
from drun.template import render_template


class GrafanaClient(BaseGrafanaClient):
    """
    Grafana API client for working with models
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
        super(GrafanaClient, self).__init__(base, user, password)

    def remove_dashboard_for_model(self, model_id):
        """
        Remove model's dashboard

        :param model_id: model id
        :type model_id: str
        :return: None
        """
        if self.is_dashboard_exists(model_id):
            dashboard = self.get_model_dashboard(model_id)
            self.delete_dashboard(dashboard['uri'])

    def is_dashboard_exists(self, model_id):
        """
        Check if model's dashboard exists

        :param model_id: model id
        :type model_id: str
        :return: bool -- is dashboard exists
        """
        return self.get_model_dashboard(model_id) is not None

    def get_model_dashboard(self, model_id):
        """
        Search for model's dashboard

        :param model_id: model id
        :type model_id: str
        :return: dict with dashboard information or None
        """
        data = self._query('/api/search/?tag=model_%s' % model_id)
        if not len(data):
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
        return self.create_dashboard_for_model_by_labels({
            'com.epam.drun.model.id': model_id,
            'com.epam.drun.model.version': model_version
        })

    def create_dashboard_for_model_by_labels(self, docker_container_labels):
        """
        Create model's dashboard from docker container labels

        :param docker_container_labels: Docker labels
        :type docker_container_labels: dict[str, str]
        :return: None
        """
        model_id = docker_container_labels.get('com.epam.drun.model.id', None)
        model_version = docker_container_labels.get('com.epam.drun.model.version', None)

        self.remove_dashboard_for_model(model_id)

        json_string = render_template('grafana-dashboard.json.tmpl', {
            'MODEL_ID': model_id,
        })

        dashboard = json.loads(json_string)

        payload = {
            'overwrite': False,
            'dashboard': dashboard
        }
        self._query('/api/dashboards/db', payload, 'POST')
