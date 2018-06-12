import requests
from requests.exceptions import RequestException
import re


class AirflowRestClient(object):
    SIMPLE_ROW = re.compile("'b'([^\\[\\\\]+)\\\\n")
    SIMPLE_LOG_ROW = re.compile("'b'([^\\\\]+)\\\\n")

    def __init__(self, base_url):
        if not base_url:
            raise Exception('"base_url" parameter is required')
        elif not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        if self.version().get('status', '-') != 'OK':
            raise RequestException('Rest API is not available %s' % self.base_url)

    def _get(self, path, params=None, **kwargs):
        """Sends a GET request.

            :param path: Path within API.
            :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: json-encoded content of a response, if any.
            :rtype: dict
            """
        response = requests.get(self.base_url + path, params, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestException('HTTP Code %d for "GET %s "' % (response.status_code, path))

    def _post(self, path, data=None, json=None, files=None, **kwargs):
        """Sends a POST request.

            :param path: Path within API.
            :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: json-encoded content of a response, if any.
            :rtype: dict
            """
        response = requests.post(self.base_url + path, data, json, files=files, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestException('HTTP Code %d for "POST %s "' % (response.status_code, path))

    def version(self):
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

    def rest_api_version(self):
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

    def render(self, dag_id, task_id, execution_date, subdir=None):
        """Render a task instance's template(s)
            /api?api=render&dag_id=value&task_id=value&execution_date=value&subdir=value

            :param dag_id: The id of the dag
            :param task_id: The id of the task
            :param execution_date: The execution date of the DAG (Example: 2017-01-02T03:04:05)
            :param subdir: (Optional) File location or directory from which to look for the dag
            :return: {
                  "airflow_cmd": "airflow render salesforce_fetcher_delta sf2s3_AccountCleanInfo 2018-03-02 00:00:00",
                  "arguments": {
                    "api": "render",
                    "dag_id": "salesforce_fetcher_delta",
                    "execution_date": "2018-03-02 00:00:00",
                    "task_id": "sf2s3_AccountCleanInfo"
                  },
                  "call_time": "Thu, 15 Mar 2018 10:10:25 GMT",
                  "http_response_code": 200,
                  "output": {
                    "stderr": "",
                    "stdin": "",
                    "stdout": "b'[2018-03-15 11:22:30,095] {driver.py:120} INFO ...."
                    },
                  "post_arguments": {},
                  "response_time": "Thu, 15 Mar 2018 11:22:32 GMT",
                  "status": "OK"
                }

        """
        return self._get('api?api=render', params=dict(dag_id=dag_id, task_id=task_id
                                                       , execution_date=execution_date, subdir=subdir))

    def variables(self, is_set=None, is_get=None, json='off', default=None, _import=None, export=None, delete=None):
        """CRUD operations on variables
            GET /api?api=variables&set=value&get=value&json&default=value&import=value&export=value&delete=value
            :param is_set: (Optional) Set a variable. Expected input in the form: KEY VALUE.
            :param is_get: (Optional) Get value of a variable
            :param json: (Optional) Boolean, Deserialize JSON variable
            :param default: (Optional) Default value returned if variable does not exist
            :param _import: (Optional) Import variables from JSON file
            :param export: (Optional) Export variables to JSON file
            :param delete: (Optional) Delete a variable
        """
        return self._get('api?api=render', params={'set': is_set, 'get': is_get, 'json': json, 'default': default
            , "import": _import, 'export': export, 'delete': delete})

    def connections(self, is_list='off', add=None, delete=None, conn_id=None, conn_uri=None, conn_extra=None):
        """ List/Add/Delete connections
            GET /api?api=connections&list&add&delete&conn_id=value&conn_uri=value&conn_extra=value

            :param is_list: (Optional) Boolean,List all connections
            :param add: (Optional) Boolean,Add a connection
            :param delete: (Optional) Boolean,Delete a connection
            :param conn_id: (Optional) Connection id, required to add/delete a connection
            :param conn_uri: (Optional) Connection URI, required to add a connection
            :param conn_extra: (Optional) Connection 'Extra' field, optional when adding a connection
            """

        return self._get('api?api=connections', params={'list': is_list, 'add': add, 'delete': delete, 'conn_id': conn_id
            , 'conn_uri': conn_uri, 'conn_extra': conn_extra})

    def pause(self, dag_id, subdir=None):
        """ Pauses a DAG
                GET /api?api=pause&dag_id=value&subdir=value
            :param dag_id: The id of the dag
            :param subdir: (Optional) File location or directory from which to look for the dag
            """
        return self._get('api?api=pause', params={dag_id: dag_id, subdir: subdir})

    def unpause(self, dag_id, subdir=None):
        """ Unpauses a DAG
                GET /api?api=unpause&dag_id=value&subdir=value
            :param dag_id: The id of the dag
            :param subdir: (Optional) File location or directory from which to look for the dag
            """
        return self._get('api?api=unpause', params={'dag_id': dag_id, 'subdir': subdir})

    def trigger_dag(self, dag_id, subdir=None, run_id=None, conf=None, exec_date=None):
        """ Trigger a DAG run
            GET /api?api=trigger_dag&dag_id=value&subdir=value&run_id=value&conf=value&exec_date=value

            :param dag_id: The id of the dag
            :param subdir: (Optional) File location or directory from which to look for the dag
            :param run_id: (Optional) Helps to identify this run
            :param conf: (Optional) JSON string that gets pickled into the DagRun's conf attribute
            :param exec_date: (Optional) The execution date of the DAG
            """
        return self._get('api?api=trigger_dag', params={'dag_id': dag_id, 'subdir': subdir, 'run_id': run_id
                , 'conf': conf, 'exec_date': exec_date})

    def test_dag(self, dag_id, task_id, execution_date, subdir=None, dry_run=None, task_params=None):
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
        results = self._get('api?api=test',
                            params={'dag_id': dag_id, 'task_id': task_id, 'execution_date': execution_date
                                , 'subdir': subdir, 'dry_run': dry_run, 'task_params': task_params})

        if 'output' in results and 'stderr' in results['output'] and results['output'][
            'stderr']:  # if stderr is not empty, task failed
            raise Exception('An error occured while running %s/%s with a ' % (dag_id, task_id), results['arguments']
                            ,
                            self._find_lines_in_stdout(results['output']['stderr'], first_pattern=self.SIMPLE_LOG_ROW))

        return self._find_lines_in_stdout(results['output']['stdout'], first_pattern=self.SIMPLE_LOG_ROW)

    def dag_state(self, dag_id, execution_date, subdir=None):
        """ Get the status of a dag run
            GET /api?api=dag_state&dag_id=value&execution_date=value&subdir=value

            :param dag_id: The id of the dag
            :param execution_date: The execution date of the DAG (Example: 2017-01-02T03:04:05)
            :param subdir: (Optional) File location or directory from which to look for the dag"""

        return self._get('api?api=dag_state',
                         params={'dag_id': dag_id, 'execution_date': execution_date, 'subdir': subdir})

    def list_tasks(self, dag_id, tree=None, subdir=None):
        """ List the tasks within a DAG
            GET /api?api=list_tasks&dag_id=value&tree&subdir=value

            :param dag_id: The id of the dag
            :param tree: (Optional) Boolean, Tree view
            :param subdir: (Optional) File location or directory from which to look for the dag"""

        return self._find_lines_in_stdout(self._get('api?api=list_tasks'
                                                    , params={'dag_id': dag_id, 'tree': tree, 'subdir': subdir}))

    def list_dags(self, subdir=None, report=None):
        """ List all the DAGs
            GET /api?api=list_dags&subdir=value&report

            :param subdir: (Optional) File location or directory from which to look for the dag
            :param report: (Optional) Boolean, Show DagBag loading report"""
        return self._find_lines_in_stdout(self._get('api?api=list_dags'
                                                    , params={'subdir': subdir, 'report': report}))[3:]

    def task_state(self, dag_id, task_id, execution_date, subdir=None):
        """ Get the status of a task instance
            GET /api?api=task_state&dag_id=value&task_id=value&execution_date=value&subdir=value

            :param dag_id: The id of the dag
            :param task_id: The id of the task
            :param execution_date: The execution date of the DAG (Example: 2017-01-02T03:04:05)
            :param subdir: (Optional) File location or directory from which to look for the dag"""
        return self._get('api?api=task_state', params={'dag_id': dag_id, 'task_id': task_id,
                                                       'execution_date': execution_date, 'subdir': subdir})

    def deploy_dag(self, dag_file=None, dag_file_path=None):
        """ Deploy a new DAG File to the DAGs directory
            POST /api?api=deploy_dag

            :param dag_file_path: Path to Python file to upload and deploy
            :param dag_file: Python file to upload and deploy

            """
        if dag_file_path is not None:
            return self._post('api?api=deploy_dag', files={'dag_file': open(dag_file_path)})
        elif dag_file is not None:
            return self._post('api?api=deploy_dag', files={'dag_file': dag_file})
        else:
            raise Exception('dag_file and dag_file_path can\'t be both None')

    def refresh_dag(self, dag_id):
        """ Refresh a DAG in the Web Server
            GET /api?api=refresh_dag&dag_id=value
            """
        return self._get('api?api=refresh_dag', params={'dag_id': dag_id})

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
