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

import os
import sys
import random
import tempfile
import logging

import unittest2

from legion.sdk import utils as legion_utils

# Extend PYTHONPATH in order to import test tools and models
sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import patch_config


LOGGER = logging.getLogger(__name__)


def patch_env_host_user_password(host='localhost', protocol='http', user='', password=''):
    return patch_config({
        'EXTERNAL_RESOURCE_HOST': host,
        'EXTERNAL_RESOURCE_PROTOCOL': protocol,
        'EXTERNAL_RESOURCE_USER': user,
        'EXTERNAL_RESOURCE_PASSWORD': password
    })


class TestUtilsExternalFile(unittest2.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self._work_directory = tempfile.mkdtemp()

        self._temp_file_path = os.path.join(self._work_directory, 't1')
        temp_content = str(random.random())

        with open(self._temp_file_path, 'w') as f:
            f.write(temp_content)

    def tearDown(self):
        legion_utils.remove_directory(self._work_directory)

    def test_directory_remove(self):
        temp_directory_path = os.path.join(self._work_directory, 'temp_dir')

        self.assertFalse(os.path.exists(temp_directory_path))

        os.makedirs(temp_directory_path)
        self.assertTrue(os.path.exists(temp_directory_path))

        legion_utils.remove_directory(temp_directory_path)
        self.assertFalse(os.path.exists(temp_directory_path))

    def test_external_file_save_local(self):
        target_file_path = os.path.join(self._work_directory, 't2')

        self.assertTrue(os.path.exists(self._temp_file_path))
        self.assertFalse(os.path.exists(target_file_path))

        result_path = legion_utils.save_file(self._temp_file_path, target_file_path)

        self.assertEqual(result_path, target_file_path)
        self.assertTrue(os.path.exists(self._temp_file_path))
        self.assertTrue(os.path.exists(target_file_path))


if __name__ == '__main__':
    unittest2.main()
