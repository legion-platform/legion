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
import logging
import time
from legion_test.robot.dex_client import get_session_cookies

class Airflow:
    """
    Airflow client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    SIMPLE_ROW = re.compile("'b'([^\\[\\\\]+)\\\\n")
    SIMPLE_LOG_ROW = re.compile("'b'([^\\\\]+)\\\\n")
    BASE_REST_API_URL_TEMPLATE = '%s/admin/rest_api/'
    BASE_URL_TEMPLATE = '%s/admin/'

    _TIMEOUT_SEC = 10

    logger = logging.getLogger(__name__)

    def __init__(self):
        """
        Init client
        """
        self.root_url = None  # Airflow Rest API Base url, type: str

    def connect_to_airflow(self, root_url, num_attempts=3, pause_sec=3):
        """
        Connect to Airflow Rest API

        :param root_url: Airflow Web root url.
        :type root_url: str
        :param num_attempts: Number of attempts to connect to Rest API.
        :type num_attempts: int
        :param pause_sec: Pause length in seconds between attempts to connect to Rest API.
        :type pause_sec: int
        :raise RequestException: on unavailable Rest API: if HTTP code 200 is not received
        :return None
        """
        if not root_url:
            raise Exception('"domain" parameter is required')

        self.root_url = root_url
        e = None
        for i in range(num_attempts):
            try:
                response = self.get_airflow_version()
            except RequestException as _e:
                self.logger.debug("Caught exception while checking Rest API: %s", _e)
                e = _e
            else:
                if response.get('status', '-') == 'OK':
                    return response
            time.sleep(pause_sec)
        raise RequestException('Rest API is not available %s' % root_url, e)

    def _get(self, path, params=None, use_rest_api_root=True, **kwargs):
        """Sends a GET request.
            :param path: Path within API.
            :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
            :param use_rest_api_root: (optional) Indicated, if Rest API Plugin Context Root should be added
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: json-encoded content of a response, if any.
            :rtype: dict
            """
        if use_rest_api_root:
            url = (self.BASE_REST_API_URL_TEMPLATE % self.root_url) + path
        else:
            url = (self.BASE_URL_TEMPLATE % self.root_url) + path
        response = requests.get(url, params, timeout = self._TIMEOUT_SEC, cookies=get_session_cookies(), **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestException('HTTP Code %d for "GET %s "' % (response.status_code, url))

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
        return self._find_lines_in_stdout(self._get('api?api=list_dags',
                                                    params={'subdir': subdir, 'report': report}))[3:]

    def find_airflow_tasks(self, dag_id, tree=None, subdir=None):
        """ List the tasks within a DAG
            GET /api?api=list_tasks&dag_id=value&tree&subdir=value

            :param dag_id: The id of the dag
            :param tree: (Optional) Boolean, Tree view
            :param subdir: (Optional) File location or directory from which to look for the dag"""

        return self._find_lines_in_stdout(self._get('api?api=list_tasks',
                                                    params={'dag_id': dag_id, 'tree': tree, 'subdir': subdir}))

    def trigger_airflow_task(self, dag_id, task_id, execution_date, subdir=None, dry_run=None, task_params=None):
        """ Test a task instance. This will run a task without checking for dependencies or recording
                it's state in the database.
                GET /api?api=test&dag_id=value&task_id=value&execution_date=value&subdir=value&dry_run&task_params=value

            :param dag_id: The id of the dag
            :param task_id: The id of the task
            :param execution_date: The execution date of the DAG (Example: 2017-01-02T03:04:05)
            :param subdir: (Optional) File location or directory from which to look for the dag
            :param dry_run: (Optional) Perform a dry run
            :param task_params: (Optional) Sends a JSON params dict to the task
            """
        return self._get('api?api=test',
                         params={'dag_id': dag_id, 'task_id': task_id, 'execution_date': execution_date,
                                 'subdir': subdir, 'dry_run': dry_run, 'task_params': task_params})

    def trigger_airflow_dag(self, dag_id, subdir=None, run_id=None, conf=None, exec_date=None):
        """ Trigger a DAG run
            GET /api?api=trigger_dag&dag_id=value&subdir=value&run_id=value&conf=value&exec_date=value

            :param dag_id: The id of the dag
            :param subdir: (Optional) File location or directory from which to look for the dag
            :param run_id: (Optional) Helps to identify this run
            :param conf: (Optional) JSON string that gets pickled into the DagRun's conf attribute
            :param exec_date: (Optional) The execution date of the DAG
            """
        return self._get('api?api=trigger_dag', params={'dag_id': dag_id, 'subdir': subdir, 'run_id': run_id,
                                                        'conf': conf, 'exec_date': exec_date})


    def get_failed_airflow_dags(self):
        """
        Get Failed airflow dags
        :rtype list[str]
        :return: A list of failed dags names
        """
        data = self._get('airflow/task_stats', use_rest_api_root=False)
        failed_dags = []
        for dag_id, dag_runs in data.items():
            for dag_run in dag_runs:
                if dag_run.get('color', '') == 'red' and dag_run.get('count', 0) > 0:
                    failed_dags.append(dag_id)
                    break
        return failed_dags

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
