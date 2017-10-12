"""
Graphana API functional for working with models
"""

import json

from drun.external.base_grafana_client import BaseGrafanaClient

from jinja2 import Environment, PackageLoader, select_autoescape


class GrafanaClient(BaseGrafanaClient):
    """
    Grafana API client for working with models
    """

    def __init__(self, base, user=None, password=None):
        """
        Build client
        :param base: str base url, for example: http://parallels/grafana/
        :param user: str user name or None
        :param password: str user password or None
        """
        super(GrafanaClient, self).__init__(base, user, password)

    def remove_dashboard_for_model(self, model_id):
        """
        Remove model's dashboard
        :param model_id: str model id
        :return: None
        """
        if self.is_dashboard_exists(model_id):
            dashboard = self.get_model_dashboard(model_id)
            self.delete_dashboard(dashboard['uri'])

    def is_dashboard_exists(self, model_id):
        """
        Check if model's dashboard exists
        :param model_id: str model id
        :return: bool
        """
        return self.get_model_dashboard(model_id) is not None

    def get_model_dashboard(self, model_id):
        """
        Search for model's dashboard
        :param model_id: str model id
        :return: dict with dashboard information or None
        """
        data = self._query('/api/search/?tag=model_%s' % model_id)
        if not len(data):
            return None

        return data[0]

    def create_dashboard_for_model(self, model_id, model_version=None):
        """
        Create model's dashboard from template
        :param model_id: str model id
        :param model_version: str model version
        :return: None
        """
        return self.create_dashboard_for_model_by_labels({
            'com.epam.drun.model.id': model_id,
            'com.epam.drun.model.version': model_version
        })

    def create_dashboard_for_model_by_labels(self, docker_container_labels):
        """
        Create model's dashboard from docker container labels
        :param docker_container_labels: dict of Docker labels
        :return: None
        """
        model_id = docker_container_labels.get('com.epam.drun.model.id', None)
        model_version = docker_container_labels.get('com.epam.drun.model.version', None)

        self.remove_dashboard_for_model(model_id)

        env = Environment(
            loader=PackageLoader(__name__, 'templates'),
            autoescape=select_autoescape(['tmpl'])
        )

        template = env.get_template('graphana-dashboard.json.tmpl')
        json_string = template.render({
            'MODEL_ID': model_id,
        })

        dashboard = json.loads(json_string)

        payload = {
            'overwrite': False,
            'dashboard': dashboard
        }
        self._query('/api/dashboards/db', payload, 'POST')
