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
import unittest.mock
import json
from random import randint
import urllib.parse
from io import BytesIO
import sys
import os

from werkzeug.datastructures import FileMultiDict

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import patch_environ, ModelServeTestBuild, EDITestServer
from legion_test_models import create_simple_summation_model_by_df, \
    create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
    create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
    create_simple_summation_model_lists_with_files_info

import legion.serving.pyserve as pyserve


class TestEDI(unittest2.TestCase):
    def test_model_info_with_typed_columns(self):
        with EDITestServer() as edi:
            with unittest.mock.patch('legion.k8s.enclave.Enclave.get_models', side_effect=lambda *x, **y: []) as get_models_patched:
                models_info = edi.edi_client.inspect()
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)
                self.assertTrue(len(get_models_patched.call_args_list) == 1, 'should be exactly one call')



if __name__ == '__main__':
    unittest2.main()
