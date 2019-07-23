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

import json
import os
import sys
import unittest.mock
import urllib.parse
from io import BytesIO
from random import randint

import unittest2
from werkzeug.datastructures import FileMultiDict

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import ModelServeTestBuild
from legion_test_models import create_simple_summation_model_by_df, \
    create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
    create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
    create_simple_summation_model_lists_with_files_info
from legion.sdk.containers import headers as legion_headers
from legion.toolchain.server import pyserve


class TestModelApiEndpoints(unittest2.TestCase):
    _multiprocess_can_split_ = True

    MODEL_NAME = 'temp'
    MODEL_VERSION = '1.8'

    @staticmethod
    def _load_response_text(response):
        data = response.data

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return data

    def _parse_json_response(self, response):
        self.assertEqual(response.mimetype, 'application/json', 'Invalid response mimetype')

        data = self._load_response_text(response)
        return json.loads(data)

    def test_health_check(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            response = model.client.get(pyserve.SERVE_HEALTH_CHECK)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(self._load_response_text(response), 'OK')

    def test_model_info_with_df(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_name=self.MODEL_NAME,
                                                                  model_version=self.MODEL_VERSION))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertIn('model_name', data, 'Cannot find id field')
            self.assertIn('model_version', data, 'Cannot find version field')
            self.assertEqual(data['model_version'], self.MODEL_VERSION, 'Incorrect model version')

            self.assertIn('endpoints', data, 'Cannot find endpoints info field')
            self.assertIn('default', data['endpoints'], 'Cannot find default endpoint')

            endpoint = data['endpoints']['default']

            self.assertIn('use_df', endpoint, 'Cannot find use_df field')
            self.assertIn('input_params', endpoint, 'Cannot find input_params field')

            self.assertEqual(endpoint['use_df'], True, 'Incorrect model use_df field')
            self.assertEqual(endpoint['input_params'],
                             {'b': {'numpy_type': 'int64', 'type': 'Integer'},
                              'a': {'numpy_type': 'int64', 'type': 'Integer'}},
                             'Incorrect model input_params')

    def test_model_info_with_typed_columns(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_types) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_name=self.MODEL_NAME,
                                                                  model_version=self.MODEL_VERSION))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertIn('model_name', data, 'Cannot find id field')
            self.assertIn('model_version', data, 'Cannot find version field')
            self.assertEqual(data['model_version'], self.MODEL_VERSION, 'Incorrect model version')

            self.assertIn('endpoints', data, 'Cannot find endpoints info field')
            self.assertIn('default', data['endpoints'], 'Cannot find default endpoint')

            endpoint = data['endpoints']['default']

            self.assertIn('use_df', endpoint, 'Cannot find use_df field')
            self.assertIn('input_params', endpoint, 'Cannot find input_params field')

            self.assertEqual(endpoint['use_df'], False, 'Incorrect model use_df field')
            self.assertEqual(endpoint['input_params'],
                             {'b': {'numpy_type': 'int32', 'type': 'Integer'},
                              'a': {'numpy_type': 'int32', 'type': 'Integer'}},
                             'Incorrect model input_params')

    def test_model_info_with_untyped_columns(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_untyped) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_name=self.MODEL_NAME,
                                                                  model_version=self.MODEL_VERSION))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertIn('model_name', data, 'Cannot find id field')
            self.assertIn('model_version', data, 'Cannot find version field')
            self.assertEqual(data['model_version'], self.MODEL_VERSION, 'Incorrect model version')

            self.assertIn('endpoints', data, 'Cannot find endpoints info field')
            self.assertIn('default', data['endpoints'], 'Cannot find default endpoint')

            endpoint = data['endpoints']['default']

            self.assertIn('use_df', endpoint, 'Cannot find use_df field')
            self.assertIn('input_params', endpoint, 'Cannot find input_params field')

            self.assertEqual(endpoint['use_df'], False, 'Incorrect model use_df field')
            self.assertEqual(endpoint['input_params'], False, 'Incorrect model input_params')

    def test_model_invoke_summation_with_df(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            url = pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                      model_version=self.MODEL_VERSION) + '?a={}&b={}'.format(a, b)
            response = model.client.get(url)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_request_id_header(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)
            test_request = "bd9aba8c-ad59-11e9-a2a3-2a2ae2dbcce4"

            url = pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                      model_version=self.MODEL_VERSION) + '?a={}&b={}'.format(a, b)

            response = model.client.get(url, headers=[(legion_headers.MODEL_REQUEST_ID, test_request)])
            self.assertEqual(response.headers.get(legion_headers.MODEL_REQUEST_ID), test_request)

            response = model.client.get(url, headers=[(legion_headers.REQUEST_ID, test_request)])
            self.assertEqual(response.headers.get(legion_headers.MODEL_REQUEST_ID), test_request)

    def test_model_invoke_summation_with_df_post_request(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.post(pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                                             model_version=self.MODEL_VERSION),
                                         data={'a': a, 'b': b})
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_ignore_url_parameters_in_post_request(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            with self.assertRaisesRegex(Exception, 'Missed value for column a'):
                url = pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                          model_version=self.MODEL_VERSION) + '?a={}'.format(a)
                model.client.post(url, data={'b': b})

    def test_model_not_found_page(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            with unittest.mock.patch('legion.sdk.clients.model.ModelClient.info_url',
                                     new_callable=unittest.mock.PropertyMock) as mock:
                with self.assertRaises(Exception) as raised_exception:
                    mock.return_value = 'wrong_url'
                    model.model_client.info()

            self.assertIn('not found', str(raised_exception.exception))

    def test_model_invoke_summation_in_batch_mode(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            parameters = [{'a': randint(1, 20), 'b': randint(2, 50)} for _ in range(10)]
            expected_answer = [{'x': pair['a'] + pair['b']} for pair in parameters]

            response = model.model_client.batch(parameters)

            self.assertIsInstance(response, list, 'Result is not a list')
            self.assertListEqual(response, expected_answer, 'Invalid answer')

    def test_model_invoke_summation_with_empty_list_in_batch_mode(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            parameters = []
            expected_answer = []

            response = model.model_client.batch(parameters)

            self.assertIsInstance(response, list, 'Result is not a list')
            self.assertListEqual(response, expected_answer, 'Invalid answer')

    def test_model_invoke_summation_with_df_and_files(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.post(pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                                             model_version=self.MODEL_VERSION),
                                         data={
                                             'a': (BytesIO(str(a).encode('utf-8')), 'random file name a.txt'),
                                             'b': (BytesIO(str(b).encode('utf-8')), 'random file name b.txt')
                                         })
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_df_with_prepare(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df_with_prepare) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            url = pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                      model_version=self.MODEL_VERSION) + '?a={}&b={}'.format(a, b)
            response = model.client.get(url)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_typed_columns(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_by_types) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            url = pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                      model_version=self.MODEL_VERSION) + '?a={}&b={}'.format(a, b)
            response = model.client.get(url)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_untyped_columns(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_untyped) as model:
            payload = {
                'var_b': randint(1, 1000),
                'var_a': randint(1, 1000),
                'var_c': randint(1, 1000)
            }

            payload_string = '?' + urllib.parse.urlencode(payload)
            response = model.client.get(pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                                            model_version=self.MODEL_VERSION)
                                        + payload_string)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result is not a dict')
            self.assertDictEqual(result, {'keys': 'var_a,var_b,var_c', 'sum': sum(payload.values())})

    def test_model_invoke_summation_with_untyped_columns_and_lists_in_batch_mode(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_lists) as model:
            payloads = [
                {
                    'movie': ['Titanic', 'Avatar', 'Pulp_Fiction'],
                    'rate': [4, 3, 5]
                },
                {
                    'movie': ['Titanic', 'Avatar', 'Pulp_Fiction'],
                    'rate': [3, 2, 1]
                }
            ]

            expected_result = [
                {'worth': 'Avatar', 'best': 'Pulp_Fiction'},
                {'worth': 'Pulp_Fiction', 'best': 'Titanic'}
            ]

            result = model.model_client.batch(payloads)

            self.assertIsInstance(result, list, 'Result not a list')
            self.assertListEqual(result, expected_result)

    def test_model_invoke_summation_with_untyped_columns_and_lists(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_lists) as model:
            payload = {
                'movies': ['Titanic', 'Avatar', 'Pulp_Fiction'],
                'ratings': [4, 3, 5]
            }

            payload_string = '?'
            payload_string += '&'.join('movie[]=' + str(value) for value in payload['movies'])
            payload_string += '&' + '&'.join('rate[]=' + str(value) for value in payload['ratings'])

            response = model.client.get(pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                                            model_version=self.MODEL_VERSION)
                                        + payload_string)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'worth': 'Avatar', 'best': 'Pulp_Fiction'})

    def test_model_invoke_summation_with_untyped_columns_and_lists_with_files_info(self):
        with ModelServeTestBuild(self.MODEL_NAME, self.MODEL_VERSION,
                                 create_simple_summation_model_lists_with_files_info) as model:
            films = {
                'Titanic': 4,
                'Avatar': 3,
                'Pulp_Fiction': 5,
            }

            files = FileMultiDict()
            for film, rate in films.items():
                content = '{}\n{}'.format(film, rate)
                file_name = 'random file name {}.txt'.format(film)

                files.add('file[]', (BytesIO(str(content).encode('utf-8')), file_name))

            response = model.client.post(pyserve.SERVE_INVOKE_DEFAULT.format(model_name=self.MODEL_NAME,
                                                                             model_version=self.MODEL_VERSION),
                                         data=files)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'worth': 'Avatar', 'best': 'Pulp_Fiction'})


if __name__ == '__main__':
    unittest2.main()
