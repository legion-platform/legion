from legion_test.grafana import GrafanaClient

import requests


class Grafana:
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        self._url = None  # type: str
        self._user = None  # type: str
        self._password = None  # type: str
        self._client = None  # type: legion_test.grafana.GrafanaClient

    def connect_to_grafana(self, domain, user, password):
        self._url = domain.strip('/')
        self._user = user
        self._password = password
        self._client = GrafanaClient(self._url, self._user, self._password)

    def dashboard_should_exists(self, model_id):
        if not self._client:
            raise Exception('Grafana client has not been initialized')

        if not self._client.is_dashboard_exists(model_id):
            raise Exception('Dashboard not exists')

    def metric_should_be_presented(self, model_id):
        url = '{}/api/datasources/proxy/1/render'.format(self._url)

        auth = None
        if self._user and self._password:
            auth = (self._user, self._password)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {
            'target': 'alias(hitcount(stats.legion.model.{}.request.count, \'1s\'), \'hit\')'.format(model_id),
            'from': '-5min',
            'until': 'now',
            'format': 'json',
            'cacheTimeout': 0,
            'maxDataPoints': 1000
        }

        response = requests.post(url, data=payload, headers=headers, auth=auth)
        data = response.json()
        data = [i[0] for i in data[0]['datapoints'] if i[0] is not None]
        if not data or max(data) < 1:
            raise Exception('Cannot find any request in grafana history')
