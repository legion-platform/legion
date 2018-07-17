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
from __future__ import print_function

from argparse import Namespace

try:
    from .legion_test_utils import ModelTestDeployment, patch_environ, get_latest_distribution
    from .legion_test_models import create_simple_summation_model_by_df
except ImportError:
    from legion_test_utils import ModelTestDeployment, patch_environ, get_latest_distribution
    from legion_test_models import create_simple_summation_model_by_df

import legion.config
import legion.containers.docker
import legion.io
import legion.model.client
import legion.model.model_id

import unittest2


class TestDeploy(unittest2.TestCase):
    MODEL_ID = 'temp'
    MODEL_VERSION = '1.8'

    def setUp(self):
        common_arguments = Namespace(docker_network=None)
        self.client = legion.containers.docker.build_docker_client(common_arguments)
        self.wheel_path = get_latest_distribution()

    def tearDown(self):
        pass

    def test_model_simple_summation_model_by_df(self):
        with ModelTestDeployment(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df, self.wheel_path) as deployment:
            self.assertEqual(deployment.model_information['version'], self.MODEL_VERSION, 'Incorrect model version')
            self.assertEqual(deployment.model_information['use_df'], True, 'Incorrect model use_df field')
            self.assertDictEqual(deployment.model_information['input_params'],
                                 {'b': {'numpy_type': 'int64', 'type': 'Integer'},
                                  'a': {'numpy_type': 'int64', 'type': 'Integer'}},
                                 'Incorrect model input_params')

            a = 10
            b = 20

            result = deployment.client.invoke(a=a, b=b)
            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})


if __name__ == '__main__':
    unittest2.main()
