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
Robot test library - flower
"""
import requests
from requests.exceptions import RequestException
from legion_test.robot.dex_client import get_session_cookies
from legion_test.utils import wait_until


class Flower:
    """
    Flower client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    WORKERS_URL = '/dashboard?json=1'

    _TIMEOUT_SEC = 10

    def __init__(self):
        """
        Init client
        """
        self.base_url = None  # Flower Base url, type: str

    def connect_to_flower(self, base_url):
        """
        Connect to Flower

        :param base_url: Flower Web root url, e.g. http://flower.cluster
        :type base_url: str
        :return None
        """
        if not base_url:
            raise Exception('"base_url" parameter is required')

        self.base_url = base_url

    def _get(self, path, params=None, parse_json=True, **kwargs):
        """Sends a GET request.
            :param path: Path within API.
            :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: json-encoded content of a response, if any.
            :param parse_json: Indicates, if response should be parsed into Json
            :type parse_json: bool
            :rtype: dict or str
            """
        response = requests.get(self.base_url + path, params, timeout=self._TIMEOUT_SEC, cookies=get_session_cookies(),
                                **kwargs)
        if response.status_code == 200:
            if parse_json:
                return response.json()
            else:
                return response
        else:
            raise RequestException('HTTP Code %d for "GET %s "' % (response.status_code, path))

    def check_if_flower_online(self):
        """
        Checks if Flower website online and returns HTTP Code 200

        :return None
        :exception RequestException if website is unavailable
        """
        self._get('/', parse_json=False)

    def get_number_of_workers_from_flower(self):
        """
        Gets the number of online workers from Flower dashboard
        :return A number of online workers
        :rtype int
        """
        response = self._get(self.WORKERS_URL)
        workers_number = 0
        if response.get('data', []):
            for item in response.get('data'):
                if item.get('status', False) is True:
                    workers_number += 1

        print("Online workers number in flower is {}".format(workers_number))
        return workers_number

    def wait_for_worker_is_ready(self, expected_count=1):
        """
        Wait until expected count of Flower workers started

        :param int or str expected_count: expected num of online Flower workers
        :return: None
        """
        expected_count = int(expected_count)
        worker_ready = wait_until(lambda: self.get_number_of_workers_from_flower() == expected_count,
                                  iteration_duration=10, iterations=30)
        if not worker_ready:
            raise Exception("Expected ready workers count '{}' does not match actual '{}'"
                            .format(expected_count, self.get_number_of_workers_from_flower()))
