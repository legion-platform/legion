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
Base Grafana HTTP API client
"""
import json
import requests


class BaseGrafanaClient:
    """
    Base Grafana HTTP API client
    """

    def __init__(self, base, user=None, password=None):
        """
        Build client
        :param base: str base url, for example: http://parallels/grafana/
        :param user: str user name or None
        :param password: str user password or None
        """
        self._base = base.strip('/')
        self._user = user
        self._password = password

    def _query(self, url, payload=None, action='GET'):
        """
        Perform query to Grafana server
        :param url: query suburl, for example: /api/search/
        :param payload: dict with payload (will be converted to JSON) or None
        :param action: str HTTP method (GET, POST, PUT, DELETE)
        :return: dict of response content
        """
        full_url = self._base + url

        headers = {
            'Content-Type': 'application/json'
        }

        auth = None
        if self._user and self._password:
            auth = (self._user, self._password)

        response = requests.request(action.lower(), full_url, json=payload, headers=headers, auth=auth)

        if response.status_code in (401, 403):
            raise Exception('Auth failed')

        if response.status_code != 200:
            raise Exception('Wrong answer for url = %s: %s' % (full_url, repr(response)))

        answer = json.loads(response.text)

        return answer

    def delete_dashboard(self, dashboard_uri):
        """
        Delete dashboard by url
        :param dashboard_uri: str dashboard uri
        :return: None
        """
        self._query('/api/dashboards/%s' % dashboard_uri, action='DELETE')
