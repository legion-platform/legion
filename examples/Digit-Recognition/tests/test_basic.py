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

from legion.model import ModelClient, load_image
from legion.external.edi import build_client
import legion.config

import unittest2


class BasicTest(unittest2.TestCase):
    def setUp(self):
        self._client = ModelClient(legion.config.MODEL_ID, legion.config.MODEL_VERSION,
                                   token=build_client().get_token(legion.config.MODEL_ID, legion.config.MODEL_VERSION))

    def test_nine_decode(self):
        image = load_image(os.path.join('files', 'nine.png'))
        response = self._client.invoke(image=image)
        self.assertEqual(response['digit'], 9)


if __name__ == '__main__':
    unittest2.main()
