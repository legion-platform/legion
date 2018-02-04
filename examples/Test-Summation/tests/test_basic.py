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
import random
import os

from legion.model.model_tests import ModelUnitTests
import legion.config

import unittest2


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel(os.environ.get(*legion.config.MODEL_ID))

    def test_random_sum(self):
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        response = self._query_model(a=a, b=b)

        self.assertEqual(response['result'], a + b)


if __name__ == '__main__':
    unittest2.main()
