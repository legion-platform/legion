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

import unittest2
import logging
import sys
import json
import argparse

import drun.pyserve as pyserve


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        self.app = pyserve.init_application(argparse.Namespace())
        self.app.testing = True
        self.client = self.app.test_client()

    def _parse_json_response(self, response):
        self.assertEqual(response.mimetype, 'application/json', 'Invalid response mimetype')

        data = response.data

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return json.loads(data)

    def test_model_info(self):
        resp = self.client.get('/api/model/dummy-model/info')
        data = self._parse_json_response(resp)

        self.assertDictEqual(data, {'version': 'dummy'})

    def test_model_invoke(self):
        resp = self.client.post('/api/model/dummy-model/invoke', data={
            'result': "It's working!",
            'age': 35
        })
        data = self._parse_json_response(resp)

        self.assertDictEqual(data, {'result': 'It\'s working!'})


if __name__ == '__main__':
    unittest2.main()
