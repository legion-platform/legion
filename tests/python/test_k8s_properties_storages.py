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
from __future__ import print_function

import warnings
import logging
import time

import unittest2
import unittest.mock
import kubernetes
import kubernetes.client.models.v1_namespace
import kubernetes.client.models.v1_object_meta

import legion.k8s
import legion.k8s.utils
import legion.k8s.definitions
import legion.config
import legion.external
import legion.template_plugins
import legion_test.profiler_loader
import legion_test.utils


warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = legion_test.profiler_loader.get_variables()

TEST_ENCLAVE_NAME = 'kirill-test'
LOGGER = logging.getLogger(__name__)


class TestK8SPropertiesStorage(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context, delete Enclave if present

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

        legion.k8s.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(legion.k8s.CONNECTION_CONTEXT))

        try:
            pass
            # legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete()
        except:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            pass
            # legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete()
        except:
            pass

    def test_create_and_read_config_map_storage(self):
        """
        Create and validate config map storage

        :return: None
        """
        storage_name = 't1'

        storage_to_write = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)

        storage_to_write.remove()

        storage_to_write['abc'] = '123'
        storage_to_write.write()

        storage_to_read = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)
        storage_to_read.read()

        self.assertEqual(storage_to_read['abc'], '123')

    @unittest2.skip
    def test_watch_enclaves(self):
        """
        Check enclave watching

        :return: None
        """
        storage = legion.k8s.K8SConfigMapStorage('abc', TEST_ENCLAVE_NAME)
        storage.read()
        storage['a'] = 'abc'

        print('YEP')


if __name__ == '__main__':
    unittest2.main()
