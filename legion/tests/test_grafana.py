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
from __future__ import print_function

import os

import legion.config
import legion.external.grafana as grafana
import unittest2


class TestGrafana(unittest2.TestCase):
    def setUp(self):
        host = os.environ.get(*legion.config.GRAFANA_URL)
        user = os.environ.get(*legion.config.GRAFANA_USER)
        password = os.environ.get(*legion.config.GRAFANA_PASSWORD)
        self.client = grafana.GrafanaClient(host, user, password)

    def test_dashboard_creation(self):
        model_id = 'test_grafana'
        if self.client.is_dashboard_exists(model_id):
            self.client.remove_dashboard_for_model(model_id)

        self.client.create_dashboard_for_model(model_id, '2.0')

        self.assertTrue(self.client.is_dashboard_exists(model_id))


if __name__ == '__main__':
    unittest2.main()
