"""
Graphana API functional
"""

import json

from drun.external.base_grafana_client import BaseGrafanaClient

from jinja2 import Environment, PackageLoader, select_autoescape


class GrafanaClient(BaseGrafanaClient):
    def __init__(self, *args, **kwargs):
        super(GrafanaClient, self).__init__(*args, **kwargs)

    def remove_dashboard_for_model(self, model_id):
        if self.is_dashboard_exists(model_id):
            self.delete_dashboard(model_id)

    def create_dashboard_for_model(self, model_id, model_version=None):
        self.remove_dashboard_for_model(model_id)

        env = Environment(
            loader=PackageLoader(__name__, '../templates'),
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




