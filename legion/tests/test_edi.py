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

import sys
import os

import unittest2
import unittest.mock
from werkzeug.datastructures import FileMultiDict

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import patch_environ, ModelServeTestBuild, EDITestServer, \
    mock_swagger_function_response_from_file as m_func, \
    persist_swagger_function_response_to_file as p_func
from legion_test_models import create_simple_summation_model_by_df, \
    create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
    create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
    create_simple_summation_model_lists_with_files_info

import legion.serving.pyserve as pyserve
import legion.k8s.services


class TestEDI(unittest2.TestCase):
    def test_edi_inspect_all_detail(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'two_models'):
                models_info = edi.edi_client.inspect()
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 2)
                # Test model #1 fields
                self.assertEqual(models_info[0].image,
                                 'localhost:31111/legion_model/recognize-digits:1.0-181019104009.1.dc59b83')
                self.assertEqual(models_info[0].model, 'recognize-digits')
                self.assertEqual(models_info[0].version, '1.0')
                self.assertEqual(models_info[0].scale, 1)
                self.assertEqual(models_info[0].ready_replicas, 1)
                self.assertEqual(models_info[0].namespace, 'debug-enclave')
                # Test model #2 fields
                self.assertEqual(models_info[1].image,
                                 'localhost:31111/legion_model/test-summation:1.0-181019103731.1.dc59b83')
                self.assertEqual(models_info[1].model, 'test-summation')
                self.assertEqual(models_info[1].version, '1.0')
                self.assertEqual(models_info[1].scale, 1)
                self.assertEqual(models_info[1].ready_replicas, 1)
                self.assertEqual(models_info[1].namespace, 'debug-enclave')

    def test_edi_inspect_filter_empty_results(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'two_models'):
                models_info = edi.edi_client.inspect('unexisted-model-id')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)


if __name__ == '__main__':
    unittest2.main()
