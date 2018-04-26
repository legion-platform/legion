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
Robot test library - airflow
"""
import re
import requests
from requests.exceptions import RequestException


class Airflow:
    """
    Airflow client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    SIMPLE_ROW = re.compile("'b'([^\\[\\\\]+)\\\\n")
    SIMPLE_LOG_ROW = re.compile("'b'([^\\\\]+)\\\\n")
    BASE_URL_TEMPLATE = '%s/admin/rest_api/'

    _TIMEOUT_SEC = 10

    def __init__(self):
        """
        Init client
        """
        self.base_url = None  # Airflow Rest API Base url, type: str

    def connect_to_airflow(self, root_url):
        """
        Connect to Airflow Rest API

        :param root_url: Airflow Web root url.
        :type root_url: str
        :return None
        """
        if not root_url:
            raise Exception('"domain" parameter is required')

        self.base_url = self.BASE_URL_TEMPLATE % root_url

        if self.get_airflow_version().get('status', '-') != 'OK':
            raise RequestException('Rest API is not available %s' % self.base_url)

    def _get(self, path, params=None, **kwargs):
        """Sends a GET request.
            :param path: Path within API.
            :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: json-encoded content of a response, if any.
            :rtype: dict
            """
        response = requests.get(self.base_url + path, params, timeout = self._TIMEOUT_SEC, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestException('HTTP Code %d for "GET %s "' % (response.status_code, path))

    def get_airflow_version(self):
        """Displays the version of Airflow you're using
            :return: {
                  "arguments": {
                    "api": "version"
                  },
                  "call_time": "Thu, 15 Mar 2018 10:10:25 GMT",
                  "http_response_code": 200,
                  "output": "1.9.0",
                  "post_arguments": {},
                  "response_time": "Thu, 15 Mar 2018 10:51:53 GMT",
                  "status": "OK"
                }
        """
        return self._get('api?api=version')

    def get_airflow_rest_api_version(self):
        """Displays the version of this REST API Plugin you're using
            :return: {
              "arguments": {
                "api": "rest_api_plugin_version"
              },
              "call_time": "Thu, 15 Mar 2018 10:10:25 GMT",
              "http_response_code": 200,
              "output": "1.0.4",
              "post_arguments": {},
              "response_time": "Thu, 15 Mar 2018 11:16:10 GMT",
              "status": "OK"
            }
        """

        return self._get('api?api=rest_api_plugin_version')

    def find_airflow_dags(self, subdir=None, report=None):
        """ List all the DAGs
            GET /api?api=list_dags&subdir=value&report
            :param subdir: (Optional) File location or directory from which to look for the dag
            :param report: (Optional) Boolean, Show DagBag loading report"""
        return self._find_lines_in_stdout(self._get('api?api=list_dags'
                                                    , params={'subdir': subdir, 'report': report}))[3:]

    @staticmethod
    def _find_lines_in_stdout(response, first_pattern=SIMPLE_ROW, second_pattern=None):
        obj = response
        if type(obj) != str and 'output' in obj:
            obj = obj['output']
        if type(obj) != str and 'stdout' in obj:
            obj = obj['stdout']
        if type(obj) == str:
            lines = []
            for match in first_pattern.finditer(obj):
                if second_pattern is None:
                    lines.append(match.group(1))
                else:
                    line = match.group(1)
                    result = second_pattern.search(line)
                    if result is not None:
                        lines.append(result.group(1))

        return lines
