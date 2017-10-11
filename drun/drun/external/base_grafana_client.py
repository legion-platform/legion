import json
import requests


class BaseGrafanaClient:
    def __init__(self, base, user=None, password=None):
        self._base = base.strip('/')
        self._user = user
        self._password = password

    def _query(self, url, payload=None, action='GET'):
        full_url = self._base + url

        headers = {
            'Content-Type': 'application/json'
        }

        auth = None
        if self._user and self._password:
            auth = (self._user, self._password)

        response = requests.request(action.lower(), full_url, json=payload, headers=headers, auth=auth)
        answer = json.loads(response.text)

        return answer

    def delete_dashboard(self, model_id):
        dashboard = self.get_model_dashboard(model_id)
        self._query('/api/dashboards/%s' % dashboard['uri'], action='DELETE')

    def is_dashboard_exists(self, model_id):
        return self.get_model_dashboard(model_id) is not None

    def get_model_dashboard(self, model_id):
        data = self._query('/api/search/?tag=model_%s' % model_id)
        if not len(data):
            return None

        return data[0]