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
from unittest.mock import patch

import requests
import responses
import unittest2
from legion.sdk import config
from legion.sdk.clients.model import ModelClient


class TestModelClient(unittest2.TestCase):
    _multiprocess_can_split_ = True

    MODEL_NAME = 'temp'
    MODEL_VERSION = '1.8'

    def test_client_building(self):
        client = ModelClient(url='localhost')
        root_url = 'localhost/api/model'
        self.assertEqual(client.api_url, root_url)
        self.assertEqual(client.info_url, root_url + '/info')
        self.assertEqual(client.build_batch_url(), root_url + '/batch')
        self.assertEqual(client.build_batch_url('abcd'), root_url + '/batch/abcd')
        self.assertEqual(client.build_invoke_url(), root_url + '/invoke')
        self.assertEqual(client.build_invoke_url('abcd'), root_url + '/invoke/abcd')

    def test_client_building_from_env(self):
        with patch('legion.sdk.config.MODEL_HOST', 'test:10'):
            client = ModelClient(config.MODEL_HOST)
            root_url = 'test:10/api/model'
            self.assertEqual(client.api_url, root_url)
            self.assertEqual(client.info_url, root_url + '/info')
            self.assertEqual(client.build_invoke_url(), root_url + '/invoke')

    @responses.activate
    def test_client_request_retry_on_error(self):
        url = 'http://some_url.com'
        responses.add(responses.GET, url, body=requests.RequestException('Some exception'))
        content = 'some content'
        responses.add(responses.GET, url, status=200, body=content)
        client = ModelClient(self.MODEL_NAME, self.MODEL_VERSION)
        res = client._request('get', url)
        self.assertEqual(res, content)


if __name__ == '__main__':
    unittest2.main()
