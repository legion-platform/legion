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

<<<<<<< HEAD:legion_test/legion_test/robot/grafana.py
from legion_test.grafana import GrafanaClient
from legion_test.robot.dex_client import get_session_cookies
=======
from legion.robot.grafana import GrafanaClient
from legion.robot.utils import normalize_name, wait_until
from legion.robot.libraries.dex_client import get_session_cookies
>>>>>>> [#849] sync files with Refactoring:legion/robot/legion/robot/libraries/grafana.py


class Grafana:
    """
    Grafana client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        """
        Init client
        """
        self._url = None  # type: str
        self._user = None  # type: str
        self._password = None  # type: str
<<<<<<< HEAD:legion_test/legion_test/robot/grafana.py
        self._client = None  # type: legion_test.grafana.GrafanaClient
=======
        self._client = None  # type: GrafanaClient
        self._start_time = time.time()
>>>>>>> [#849] sync files with Refactoring:legion/robot/legion/robot/libraries/grafana.py

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

    def get_dashboard_by(self, uid):
        """
        Get dashboard json by dashboard uid

        :param uid: a dashboard uid
        :type uid: str
        :return: dashboard json - dict[str, Any]
        """
        return self._client.get_dashboard_by(uid)

    def get_preferences(self):
        """
        Get grafana preferences

        :return: grafana response - dict[str, Any]
        """
        return self._client.get_preferences()
