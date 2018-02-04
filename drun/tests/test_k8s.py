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
import os.path

import drun.containers.k8s
import drun.config
import unittest2


class TestK8S(unittest2.TestCase):

    def setUp(self):
        self.data_directory = os.path.join(os.path.dirname(__file__), 'data')
        self.state = os.path.join(self.data_directory, 'state.yaml')
        self.secrets = os.path.join(self.data_directory, 'secrets')

    def test_secrets_loading(self):
        secrets = drun.containers.k8s.load_secrets(self.secrets)
        valid = {'grafana.user': 'admin', 'grafana.password': 'test-password'}
        self.assertIsInstance(secrets, dict)
        self.assertDictEqual(secrets, valid)

    def test_cluster_config_loading(self):
        config = drun.containers.k8s.load_config(self.state)
        valid = {'grafana': {'port': 123, 'domain': 'drun-grafana.default.svc.cluster.local'}}
        self.assertIsInstance(config, dict)
        self.assertDictEqual(config, valid)


if __name__ == '__main__':
    unittest2.main()
