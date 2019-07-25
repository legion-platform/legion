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
Robot test library - prometheus
"""
import time

import requests
from legion.robot.libraries.dex_client import get_session_cookies
from legion.robot.utils import wait_until


class Prometheus:
    """
    Prometheus client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, url):
        """
        Init client
        """
        self._url = url

    def _get_model_metric(self, model_name, model_version, model_endpoint='default'):
        """
        Get model metric data and returns it

        :param model_name: model name
        :type model_name: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :return: list[dict], list with dict with metrics
        """
        url = f'{self._url}/api/v1/query_range'
        print(f'Get metrics for model_name: "{model_name}", model_version: "{model_version}",'
              f' model_endpoint: "{model_endpoint}"')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        query = f'legion_model_metrics{{model_name="{model_name}"}}'

        params = {'query': query, 'start': time.time() - 10000, 'end': time.time() + 10000, 'step': 14}
        response = requests.post(url, params=params, headers=headers, cookies=get_session_cookies())
        response.raise_for_status()

        print(f'Loading {query} metrics. Data: {response.text}')

        return response.json()

    def metric_should_be_presented(self, model_name, model_version, model_endpoint='default'):
        """
        Check that requests count metric for model exists

        :param model_name: model name
        :type model_name: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """
        data = self._get_model_metric(model_name, model_version, model_endpoint=model_endpoint)
        if not data:
            raise Exception('Data is empty')

        datapoints = data['data']['result']

        # 0 -> one metric
        # 1 -> value of metric
        for val in map(lambda x: x['values'][0][1], datapoints):
            if val is not None and float(val) > 0:
                break
        else:
            raise Exception('Cannot find any value > 0')

    def ensure_metric_present(self, model_name, model_version, model_endpoint='default'):
        """
        Ensure that requests count metric for model exists

        :param model_name: model name
        :type model_name: str
        :param model_version: model version
        :type model_version: str
        :param model_endpoint: model endpoint
        :type model_endpoint: str
        :raises: Exception
        :return: None
        """
        def is_metric_present():
            try:
                self.metric_should_be_presented(model_name, model_version, model_endpoint=model_endpoint)
            except Exception as e:
                print('Got metric_should_be_presented exception: {}'.format(e))
                return False
            return True

        if not wait_until(is_metric_present, 5, 20):
            raise Exception('Metric is not present')
