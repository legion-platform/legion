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
import os

from legion.model.model_tests import ModelUnitTests
import legion.config

import unittest2


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel(os.environ.get(*legion.config.MODEL_ID))

    def test_nine_decode(self):
        image = self._load_image(os.path.join('files', 'nine.png'))
        response = self._query_model(image=image)
        self.assertEqual(response['digit'], 9)


if __name__ == '__main__':
    unittest2.main()
