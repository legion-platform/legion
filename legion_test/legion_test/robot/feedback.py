#
#    Copyright 2018 EPAM Systems
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
Robot test library - feedback
"""
import json

import requests


class Feedback:
    """
    Feedback client for robot tests
    """

    @staticmethod
    def send_feedback_data(domain, event, time=None, **payload):
        """
        Connect to grafana server

        :param domain: feedback domain
        :type domain: str
        :param event: event name
        :type event: str
        :param time: timestamp, by default - skipped
        :type time: str
        :param payload: payload data
        :type payload: str
        :return: None
        """
        url = '{}/{}'.format(domain, event)

        data = {
            'json': json.dumps(payload if payload else {})
        }

        if time and time != 'now':
            data['time'] = time

        response = requests.get(url, data=data)

        if response.status_code != 200:
            raise requests.RequestException('HTTP Code %d for "GET %s "' % (response.status_code, url))
