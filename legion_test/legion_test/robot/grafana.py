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
Robot test library - grafana
"""
from legion_test.grafana import GrafanaClient
from legion_test.utils import normalize_name, wait_until
from legion_test.robot.dex_client import get_session_cookies
import requests


class Grafana:
    """
    Grafana client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        """
        Init client
        """
        self._url = None  # type: str
        self._user = None  # type: str
        self._password = None  # type: str
        self._client = None  # type: legion_test.grafana.GrafanaClient

    def connect_to_grafana(self, domain, user, password):
        """
        Connect to grafana server

        :param domain: domain name
        :type domain: str
        :param user: login
        :type user: str
        :param password: password
        :type password: str
        :return: None
        """
        self._url = domain.strip('/')
        self._user = user
        self._password = password
        self._client = GrafanaClient(self._url, self._user, self._password)
        self._client.set_cookies(get_session_cookies())

    def dashboard_should_exists(self, model_id):
        """
        Check that dashboard for model exists

        :param model_id: model ID
        :type model_id: str
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Grafana client has not been initialized')

        if not self._client.is_dashboard_exists(model_id):
            raise Exception('Dashboard not exists')

    def dashboard_should_not_exists(self, model_id):
        """
        Check that dashboard for model does not exist

        :param model_id: model ID
        :type model_id: str
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Grafana client has not been initialized')

        if self._client.is_dashboard_exists(model_id):
            raise Exception('Dashboard exists')

    def _get_model_metric(self, model_id, model_version, model_endpoint='default'):
        """
        Gets model metric data and returns it
        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :return: list[dict], list with dict with metrics
        """

        url = '{}/api/datasources/proxy/1/render'.format(self._url)

        auth = None
        if self._user and self._password:
            auth = (self._user, self._password)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        model_identifier = '{}.{}.{}'.format(normalize_name(model_id, dns_1035=True),
                                             normalize_name(model_version, dns_1035=True),
                                             normalize_name(model_endpoint, dns_1035=True))

        target = 'highestMax(stats.legion.model.{}.request.count, 1)'.format(model_identifier)

        payload = {
            'target': target,
            'from': '-5min',
            'until': 'now',
            'format': 'json',
            'cacheTimeout': 0,
            'maxDataPoints': 1000
        }

        response = requests.post(url, data=payload, headers=headers, auth=auth, cookies=get_session_cookies())
        print('Loading {} metrics. Data: {}'.format(target, response.text))

        return response.json()

    def metric_should_be_presented(self, model_id, model_version, model_endpoint='default'):
        """
        Check that requests count metric for model exists

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """

        data = self._get_model_metric(model_id, model_version, model_endpoint=model_endpoint)
        if not data:
            raise Exception('Data is empty')

        datapoints = data[0]['datapoints']

        for val, time in datapoints:
            if val is not None and val > 0:
                break
        else:
            raise Exception('Cannot find any value > 0')

    def ensure_metric_present(self, model_id, model_version, model_endpoint='default'):
        """
        Ensure that requests count metric for model exists

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """
        def is_metric_present():
            try:
                self.metric_should_be_presented(model_id, model_version, model_endpoint=model_endpoint)
            except Exception as e:
                print('Got metric_should_be_presented exception: {}'.format(e))
                return False
            return True

        if not wait_until(is_metric_present, 5, 3):
            raise Exception('Metric is not present')

    def metric_should_not_be_presented(self, model_id, model_version, model_endpoint='default'):
        """
        Check that requests count metric for model not exists

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """

        data = self._get_model_metric(model_id, model_version, model_endpoint=model_endpoint)
        if not data:
            return

        datapoints = data[0]['datapoints']

        for val, time in datapoints:
            if val is not None and val > 0:
                raise Exception('Metric is present')

    def ensure_metric_not_present(self, model_id, model_version, model_endpoint='default'):
        """
        Ensure that requests count metric for model not exists

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """
        def is_metric_present():
            try:
                self.metric_should_not_be_presented(model_id, model_version, model_endpoint=model_endpoint)
            except Exception as e:
                print('Got metric_should_not_be_presented exception: {}'.format(e))
                return True
            return False

        if wait_until(is_metric_present, 5, 3):
            raise Exception('Metric is not present')
