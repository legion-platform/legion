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
from nose.plugins.attrib import attr

import legion.k8s
import legion.k8s.utils
import legion.k8s.definitions
import legion.config
import legion.external
import legion.model
import legion.template_plugins
import legion_test.utils
import legion_test.profiler_loader


warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = legion_test.profiler_loader.get_variables()

TEST_ENCLAVE_NAME = 'properties-storage'
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

        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        current_namespace_name = VARIABLES['ENCLAVES'][0]
        current_namespace = core_api.read_namespace(current_namespace_name)

        try:
            new_namespace_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
                name=TEST_ENCLAVE_NAME, labels={
                    legion.k8s.definitions.ENCLAVE_NAMESPACE_LABEL: TEST_ENCLAVE_NAME
                })
            new_namespace = kubernetes.client.models.v1_namespace.V1Namespace(
                spec=current_namespace.spec, metadata=new_namespace_metadata)

            LOGGER.info('Creating namespace {}'.format(TEST_ENCLAVE_NAME))
            core_api.create_namespace(new_namespace)
        except Exception as exception:
            LOGGER.info('Cannot create namespace {} that should be built for testing: {}'
                        .format(TEST_ENCLAVE_NAME, exception))

    @classmethod
    def tearDownClass(cls):
        try:
            LOGGER.info('Deleting namespace {}'.format(TEST_ENCLAVE_NAME))
            legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete()
        except Exception as exception:
            LOGGER.info('Cannot delete namespace {} that has been built for testing: {}'
                        .format(TEST_ENCLAVE_NAME, exception))

    @attr('k8s', 'props')
    def test_overwrite_config_map_storage(self):
        """
        Overwrite config map storage on save

        :return:
        """
        pass

    @attr('k8s', 'props')
    def test_read_config_map_with_update_on_timeout(self):
        """
        Update config map on timeouts

        :return:
        """
        pass

    @attr('k8s', 'props')
    def test_write_and_listing_config_map(self):
        """
        Listing config map

        :return:
        """
        storage_name = 'rw-storage'

        storage_to_write = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)
        storage_to_write.save()

        self.assertIn(storage_name, legion.k8s.K8SConfigMapStorage.list(TEST_ENCLAVE_NAME))

        storage_to_write.destroy()

    @attr('k8s', 'props')
    def test_retrive_config_map(self):
        """
        Retrive and load config map in one instruction

        :return:
        """
        storage_name = 'rw-retrive-storage'

        storage_to_write = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)
        storage_to_write['test_str'] = 'abc'
        storage_to_write.save()

        storage_to_read = legion.k8s.K8SConfigMapStorage.retrive(storage_name, TEST_ENCLAVE_NAME)
        self.assertEqual(storage_to_read['test_str'], 'abc')

        storage_to_read.destroy()

    @attr('k8s', 'props')
    def test_create_and_read_config_map_storage(self):
        """
        Create and read config map storage with defined fields

        :return: None
        """
        storage_name = 'rw-map-storage'

        storage_to_write = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)

        storage_to_write['int_var'] = 1233
        storage_to_write['float_var'] = 52.2354
        storage_to_write['str_var'] = 'Test string'
        storage_to_write.save()

        items = legion.k8s.K8SConfigMapStorage.list(TEST_ENCLAVE_NAME)
        self.assertIn(storage_name, items)

        storage_to_read = legion.k8s.K8SConfigMapStorage(storage_name, TEST_ENCLAVE_NAME)
        storage_to_read.load()

        self.assertEqual(storage_to_read.get('int_var', cast=legion.model.int32), 1233)
        self.assertAlmostEqual(storage_to_read.get('float_var', cast=legion.model.float32), 52.2354, 3)
        self.assertEqual(storage_to_read.get('str_var', cast=legion.model.string), 'Test string')
        self.assertEqual(storage_to_read['str_var'], 'Test string')

    @attr('k8s', 'props')
    def test_create_and_read_secret_storage(self):
        """
        Create and read secret storage with defined fields

        :return: None
        """
        storage_name = 'rw-secret-storage'

        storage_to_write = legion.k8s.K8SSecretStorage(storage_name, TEST_ENCLAVE_NAME)

        storage_to_write['int_var'] = 1233
        storage_to_write['float_var'] = 52.2354
        storage_to_write['str_var'] = 'Test string'
        storage_to_write.save()

        items = legion.k8s.K8SSecretStorage.list(TEST_ENCLAVE_NAME)
        self.assertIn(storage_name, items)

        storage_to_read = legion.k8s.K8SSecretStorage(storage_name, TEST_ENCLAVE_NAME)
        storage_to_read.load()

        self.assertEqual(storage_to_read.get('int_var', cast=legion.model.int32), 1233)
        self.assertAlmostEqual(storage_to_read.get('float_var', cast=legion.model.float32), 52.2354, 3)
        self.assertEqual(storage_to_read.get('str_var', cast=legion.model.string), 'Test string')
        self.assertEqual(storage_to_read['str_var'], 'Test string')

        storage_to_read.destroy()

        items = legion.k8s.K8SConfigMapStorage.list(TEST_ENCLAVE_NAME)
        self.assertNotIn(storage_name, items)


if __name__ == '__main__':
    unittest2.main()
