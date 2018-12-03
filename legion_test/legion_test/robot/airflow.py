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

    _TIMEOUT_SEC = 20

    logger = logging.getLogger(__name__)

    def __init__(self):
        """
        Init client
        """
        self.root_url = None  # Airflow Rest API Base url, type: str
        self.dex_cookies = None  # Dex cookies for Airflow Rest API calls, type: dict

    def connect_to_airflow(self, root_url, num_attempts=3, pause_sec=3, dex_cookies={}):
        """
        Connect to Airflow Rest API

        :param root_url: Airflow Web root url.
        :type root_url: str
        :param num_attempts: Number of attempts to connect to Rest API.
        :type num_attempts: int
        :param pause_sec: Pause length in seconds between attempts to connect to Rest API.
        :type pause_sec: int
        :param dex_cookies:  Dex Cookies if they are already received, if empty - get new for Legion static user
        :type dex_cookies: dict
        :raise RequestException: on unavailable Rest API: if HTTP code 200 is not received
        :return None
        """
        if dex_cookies:
            self.dex_cookies = dex_cookies
        if not root_url:
            raise Exception('"domain" parameter is required')

        print('Connecting to Airflow {!r}'.format(root_url))
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
        if self.dex_cookies:
            cookies = self.dex_cookies
        else:
            cookies = get_session_cookies()
        if use_rest_api_root:
            url = (self.BASE_REST_API_URL_TEMPLATE % self.root_url) + path
        else:
            url = (self.BASE_URL_TEMPLATE % self.root_url) + path
        print('Requesting Airflow URL: {!r}. Params: {!r}. KWARGS: {!r}'.format(url, params, kwargs))
        response = requests.get(url, params, timeout=self._TIMEOUT_SEC, cookies=cookies, **kwargs)
        if response.status_code == 200:
            json = response.json()
            print('Airflow response: {!r}'.format(json))
            return json
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

    def find_airflow_tasks(self, dag_id, tree=None, subdir=None):
        """ List the tasks within a DAG
            GET /api?api=list_tasks&dag_id=value&tree&subdir=value

            :param dag_id: The id of the dag
            :param tree: (Optional) Boolean, Tree view
            :param subdir: (Optional) File location or directory from which to look for the dag"""

        return self._find_lines_in_stdout(self._get('api?api=list_tasks',
                                                    params={'dag_id': dag_id,
                                                            'tree': tree,
                                                            'subdir': subdir}))

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
        status = self._get('api?api=test',
                           params={'dag_id': dag_id, 'task_id': task_id, 'execution_date': execution_date,
                                   'subdir': subdir, 'dry_run': dry_run, 'task_params': task_params})
        stderr = self._find_lines_in_stderr(status)
        if stderr:
            raise Exception("task {t} failed:\n {e}".format(t=task_id, e=stderr))
        return

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
                color = dag_run.get('color', '')
                run_count = dag_run.get('count', 0)
                print('Detected DAG {!r}. Color: {!r}, Run count: {!r}'.format(dag_id, color, run_count))
                if color == 'red' and run_count > 0:
                    failed_dags.append(dag_id)
                    break
        return failed_dags

    def get_succeeded_airflow_dags(self):
        """
        Get succeeded airflow dags
        :rtype list[str]
        :return: A list of succeeded dags names
        """
        data = self._get('airflow/task_stats', use_rest_api_root=False)
        succeeded_dags = []
        for dag_id, dag_runs in data.items():
            for dag_run in dag_runs:
                color = dag_run.get('color', '')
                run_count = dag_run.get('count', 0)
                print('Detected DAG {!r}. Color: {!r}, Run count: {!r}'.format(dag_id, color, run_count))
                if color == 'green' and run_count > 0:
                    succeeded_dags.append(dag_id)
                    break
        return succeeded_dags

    def is_dag_ready(self, dag_id, timeout=60, sleep=3):
        """
        Check if dag was loaded to airflow web

        :param str dag_id: The id of the dag
        :param int timeout: seconds to wait
        :param int sleep: seconds to sleep before retries
        :rtype boolean
        :return: if dag is on the airflow web
        """
        timeout = int(timeout)
        sleep = int(sleep)
        start = time.time()
        time.sleep(sleep)

        while True:
            data = self._get('airflow/dag_stats', use_rest_api_root=False)
            elapsed = time.time() - start
            if dag_id in data.keys():
                print('Dag {} became available after {} seconds'
                      .format(dag_id, data))
                return True
            elif elapsed > timeout > 0:
                raise Exception('Dag {} did not become available after {} seconds wait'.format(dag_id, timeout))
            else:
                print('Dag {} is not available after {} seconds'
                      .format(dag_id, elapsed))
                time.sleep(sleep)

    def get_airflow_dag_state(self, dag_id):
        """
        Get airflow dag state points
        :rtype dict
        :return: A dict with dag states
        """
        data = self._get('airflow/dag_stats', use_rest_api_root=False)
        dag_stats = data[dag_id]
        success_count = dag_stats[0]['count']
        running_count = dag_stats[1]['count']
        failed_count = dag_stats[2]['count']
        print('Detected DAG {!r}. Success tasks count: {!r}, Running tasks count: {!r}, Failed tasks count: {!r}'
              .format(dag_id, success_count, running_count, failed_count))
        return {'success': success_count, 'running': running_count, 'failed': failed_count}

    def wait_dag_finished(self, dag_id, timeout=120, sleep=5):
        """
        Wait airflow dag finished
        :rtype dict
        :return: A dict with dag states
        """
        timeout = int(timeout)
        sleep = int(sleep)
        start = time.time()
        time.sleep(sleep)

        while True:
            running_count = self.get_airflow_dag_state(dag_id)['running']
            elapsed = time.time() - start
            if running_count == 0:
                print('Dag {} is not running after {} seconds'
                      .format(dag_id, elapsed))
                return
            elif elapsed > timeout > 0:
                raise Exception('Dag {} did not finish after {} seconds wait'.format(dag_id, timeout))
            else:
                print('Dag {} is still running after {} seconds'
                      .format(dag_id, elapsed))
                time.sleep(sleep)

    def wait_dag_is_running(self, dag_id, timeout=60, sleep=5):
        """
        Wait airflow dag finished
        :rtype dict
        :return: A dict with dag states
        """
        timeout = int(timeout)
        sleep = int(sleep)
        start = time.time()
        time.sleep(sleep)

        while True:
            data = self._get('airflow/dag_stats', use_rest_api_root=False)
            elapsed = time.time() - start
            if dag_id in data.keys():
                print('Dag {} became available after {} seconds'
                      .format(dag_id, data))
                return True
            elif elapsed > timeout > 0:
                raise Exception('Dag {} did not become available after {} seconds wait'.format(dag_id, timeout))
            else:
                print('Dag {} is not available after {} seconds'.format(dag_id, elapsed))
                time.sleep(sleep)

    def _find_lines_in_stdout(self, response, first_pattern=SIMPLE_ROW, second_pattern=None):
        obj = response
        if type(obj) != str and 'output' in obj:
            obj = obj['output']
        if type(obj) != str and 'stdout' in obj:
            obj = obj['stdout']
        return self._find_lines(obj, first_pattern, second_pattern)

    def _find_lines_in_stderr(self, response, first_pattern=SIMPLE_ROW, second_pattern=None):
        obj = response
        if type(obj) != str and 'output' in obj:
            obj = obj['output']
        if type(obj) != str and 'stderr' in obj:
            obj = obj['stderr']
        return self._find_lines(obj, first_pattern, second_pattern)

    @staticmethod
    def _find_lines(response, first_pattern=SIMPLE_ROW, second_pattern=None):
        obj = response
        lines = []
        if type(obj) == str:
            for match in first_pattern.finditer(obj):
                if second_pattern is None:
                    lines.append(match.group(1))
                else:
                    line = match.group(1)
                    result = second_pattern.search(line)
                    if result is not None:
                        lines.append(result.group(1))
        return lines
