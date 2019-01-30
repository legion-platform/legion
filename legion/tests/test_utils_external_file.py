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
from unittest.mock import patch

import legion.config
import legion.utils as utils
import legion.containers.docker
import requests.auth
import responses
import unittest2

# Extend PYTHONPATH in order to import test tools and models
sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import LegionTestContainer


LOGGER = logging.getLogger(__name__)


def patch_env_host_user_password(host='localhost', protocol='http', user='', password=''):
    return patch.dict('os.environ', {
        legion.config.EXTERNAL_RESOURCE_HOST[0]: host,
        legion.config.EXTERNAL_RESOURCE_PROTOCOL[0]: protocol,
        legion.config.EXTERNAL_RESOURCE_USER[0]: user,
        legion.config.EXTERNAL_RESOURCE_PASSWORD[0]: password
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
        utils.remove_directory(self._work_directory)

    def test_directory_remove(self):
        temp_directory_path = os.path.join(self._work_directory, 'temp_dir')

        self.assertFalse(os.path.exists(temp_directory_path))

        os.makedirs(temp_directory_path)
        self.assertTrue(os.path.exists(temp_directory_path))

        utils.remove_directory(temp_directory_path)
        self.assertFalse(os.path.exists(temp_directory_path))

    def test_resource_type_detection(self):
        local_resources = (
            '/',
            '..',
            __file__
        )

        external_resources = (
            '//example.com',
            '//example.com/index.html',
            'https://example.com/index.html',
            'http://example.com/index.html',
        )

        wrong_resources = (
            'bad://example.com',
            'ftp://example.com',
        )

        for path in local_resources:
            self.assertTrue(utils.is_local_resource(path), 'Detected as external: %s' % path)

        for path in external_resources:
            self.assertFalse(utils.is_local_resource(path), 'Detected as local: %s' % path)

        for path in wrong_resources:
            with self.assertRaisesRegex(Exception, 'Unknown or unavailable resource'):
                utils.is_local_resource(path)

    @responses.activate  # pylint: disable=E1101
    def _test_external_file_reader(self, url):
        body = 'Example' * 200
        responses.add('GET', url, body=body, stream=True)  # pylint: disable=E1101

        with utils.ExternalFileReader(url) as reader:
            self.assertTrue(os.path.exists(reader.path))
            local_path = reader.path

            with open(reader.path, 'r') as page:
                content = page.read()
                self.assertEqual(body, content)

        self.assertFalse(os.path.exists(local_path))

    def test_external_file_reader_http_example(self):
        self._test_external_file_reader('http://example.com/index.html')

    def test_external_file_reader_https_example(self):
        self._test_external_file_reader('https://example.com/index.html')

    def test_external_file_reader_local(self):
        with utils.ExternalFileReader(self._temp_file_path) as reader:
            self.assertEqual(os.path.abspath(self._temp_file_path), os.path.abspath(reader.path))

        with utils.ExternalFileReader(os.path.abspath(self._temp_file_path)) as reader:
            self.assertEqual(os.path.abspath(self._temp_file_path), os.path.abspath(reader.path))

    def test_external_file_save_local(self):
        target_file_path = os.path.join(self._work_directory, 't2')

        self.assertTrue(os.path.exists(self._temp_file_path))
        self.assertFalse(os.path.exists(target_file_path))

        result_path = utils.save_file(self._temp_file_path, target_file_path)

        self.assertEqual(result_path, target_file_path)
        self.assertTrue(os.path.exists(self._temp_file_path))
        self.assertTrue(os.path.exists(target_file_path))

    def test_external_file_save_http_bin(self):
        httpbin_image = "kennethreitz/httpbin"
        LOGGER.info('Starting httpbin container from {} image...'.format(httpbin_image))

        with LegionTestContainer(image=httpbin_image, port=80) as httpbin_container:
            target_resource = 'http://localhost:{}/put'.format(httpbin_container.host_port)
            result_path = utils.save_file(self._temp_file_path, target_resource)

            self.assertEqual(target_resource, result_path)

    def test_external_file_save_by_env(self):
        target_resource = os.getenv('TEST_SAVE_URL')

        if target_resource:
            result_path = utils.save_file(self._temp_file_path, target_resource)
            self.assertEqual(target_resource, result_path)

    def test_normalize_external_resource_path(self):
        with patch_env_host_user_password('test', 'http'):
            self.assertEqual(utils.normalize_external_resource_path('///a'), 'http://test/a')

        with patch_env_host_user_password('test:8081/prefix', 'http'):
            self.assertEqual(utils.normalize_external_resource_path('///a'), 'http://test:8081/prefix/a')

        with patch_env_host_user_password('test', 'http'):
            self.assertEqual(utils.normalize_external_resource_path('///'), 'http://test/')

        with patch_env_host_user_password('demo', 'https'):
            self.assertEqual(utils.normalize_external_resource_path('http:///a'), 'http://demo/a')

        with patch_env_host_user_password('demo', 'https'):
            self.assertEqual(utils.normalize_external_resource_path('http://test/a'), 'http://test/a')

    def test_normalize_external_resource_auth(self):
        with patch_env_host_user_password(user='u1', password='p1'):
            auth = utils._get_auth_credentials_for_external_resource()
            self.assertIsInstance(auth, requests.auth.HTTPBasicAuth)
            self.assertEqual(auth.username, 'u1')
            self.assertEqual(auth.password, 'p1')

        with patch_env_host_user_password(user='', password=''):
            auth = utils._get_auth_credentials_for_external_resource()
            self.assertIsNone(auth)


if __name__ == '__main__':
    unittest2.main()
