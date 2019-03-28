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
import os

from legion.sdk.clients.model import ModelClient
from legion.sdk.clients.edi import build_client
from legion import config

import unittest2


class BasicTest(unittest2.TestCase):
    def setUp(self):
        self._client = ModelClient(config.MODEL_ID, config.MODEL_VERSION,
                                   token=build_client().get_token(config.MODEL_ID, config.MODEL_VERSION))

    def test_model(self):
        response = self._client.invoke(**{"age": "31",
                                          "capital-gain": "14084",
                                          "capital-loss": 0,
                                          "education": "Bachelors",
                                          "education-num": "13",
                                          "fnlwgt": "77516",
                                          "hours-per-week": "40",
                                          "marital-status": "Married-civ-spouse",
                                          "native-country": "United-States",
                                          "occupation": "Exec-managerial",
                                          "race": "White",
                                          "relationship": "Husband",
                                          "sex": "Male",
                                          "workclass": "Private"
                                          })

        self.assertEqual(response['result'], 1)


if __name__ == '__main__':
    unittest2.main()
