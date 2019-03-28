<<<<<<< HEAD:tests/python/test_k8s_introspection.py
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

import unittest2

import legion.k8s
import legion.k8s.utils
import legion.config
import legion.external
import legion_test.profiler_loader
import legion_test.utils
from nose.plugins.attrib import attr

warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = legion_test.profiler_loader.get_variables()
LOGGER = logging.getLogger(__name__)


class TestK8SIntrospection(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

        legion.k8s.utils.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(legion.k8s.utils.CONNECTION_CONTEXT))

    def _get_test_enclave(self):
        """
        Get test enclave

        :return: :py:class:`legion.k8s.Enclave` -- test enclave
        """
        all_enclaves = legion.k8s.find_enclaves()
        self.assertIsInstance(all_enclaves, list, 'cannot find any enclave')

        enclaves_map = {e.name: e for e in all_enclaves}
        self.assertIn(VARIABLES['MODEL_TEST_ENCLAVE'], enclaves_map, 'cannot find test enclave')
        return enclaves_map[VARIABLES['MODEL_TEST_ENCLAVE']]

    @attr('k8s', 'inspection', 'apps')
    def test_building_connection(self):
        """
        Test connection builder

        :return: None
        """
        legion.k8s.build_client()

    @attr('k8s', 'inspection', 'apps')
    def test_find_enclaves(self):
        """
        Test that we can found any enclave

        :return: None
        """
        enclaves = legion.k8s.find_enclaves()
        self.assertGreater(len(enclaves), 0, 'cannot find any enclave')

    @attr('k8s', 'inspection', 'apps')
    def test_target_enclave_presented(self):
        """
        Test that target-test enclave can be found

        :return: None
        """
        self._get_test_enclave()

    @attr('k8s', 'inspection', 'apps')
    def test_check_enclave_object(self):
        """
        Test that target-test enclave consists of all services

        :return: None
        """
        enclave = self._get_test_enclave()
        self.assertIsInstance(enclave, legion.k8s.Enclave)

        self.assertIsNotNone(enclave.edi_service, 'cannot find EDI service')
        self.assertIsNotNone(enclave.api_service, 'cannot find API (EDGE) service')

    @attr('k8s', 'inspection', 'apps')
    def test_check_edi_client(self):
        """
        Check EDI client

        :return: None
        """
        enclave = self._get_test_enclave()
        self.assertIsInstance(enclave, legion.k8s.Enclave)

        self.assertIsNotNone(enclave.edi_service, 'cannot find EDI service')
        url = enclave.edi_service.public_url
        self.assertIsNotNone(url)

        client = legion.external.RemoteEdiClient(url, token=VARIABLES['DEX_TOKEN'])
        info = client.info()
        self.assertIsInstance(info, dict)


if __name__ == '__main__':
    unittest2.main()
=======
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

import unittest2
from legion.robot import profiler_loader
from legion.sdk.clients.edi import RemoteEdiClient
from legion.sdk.k8s import utils as k8s_utils
from legion.sdk.k8s.enclave import find_enclaves, Enclave

from nose.plugins.attrib import attr

warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = profiler_loader.get_variables()
LOGGER = logging.getLogger(__name__)


class TestK8SIntrospection(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

        k8s_utils.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(k8s_utils.CONNECTION_CONTEXT))

    def _get_test_enclave(self):
        """
        Get test enclave

        :return: :py:class:`legion.k8s.Enclave` -- test enclave
        """
        all_enclaves = find_enclaves()
        self.assertIsInstance(all_enclaves, list, 'cannot find any enclave')

        enclaves_map = {e.name: e for e in all_enclaves}
        self.assertIn(VARIABLES['MODEL_TEST_ENCLAVE'], enclaves_map, 'cannot find test enclave')
        return enclaves_map[VARIABLES['MODEL_TEST_ENCLAVE']]

    @attr('k8s', 'inspection', 'apps')
    def test_building_connection(self):
        """
        Test connection builder

        :return: None
        """
        k8s_utils.build_client()

    @attr('k8s', 'inspection', 'apps')
    def test_find_enclaves(self):
        """
        Test that we can found any enclave

        :return: None
        """
        enclaves = find_enclaves()
        self.assertGreater(len(enclaves), 0, 'cannot find any enclave')

    @attr('k8s', 'inspection', 'apps')
    def test_target_enclave_presented(self):
        """
        Test that target-test enclave can be found

        :return: None
        """
        self._get_test_enclave()

    @attr('k8s', 'inspection', 'apps')
    def test_check_enclave_object(self):
        """
        Test that target-test enclave consists of all services

        :return: None
        """
        enclave = self._get_test_enclave()
        self.assertIsInstance(enclave, Enclave)

        self.assertIsNotNone(enclave.edi_service, 'cannot find EDI service')
        self.assertIsNotNone(enclave.api_service, 'cannot find API (EDGE) service')
        self.assertIsNotNone(enclave.grafana_service, 'cannot find Grafana service')
        self.assertIsNotNone(enclave.graphite_service, 'cannot find Graphite service')

    @attr('k8s', 'inspection', 'apps')
    def test_check_edi_client(self):
        """
        Check EDI client

        :return: None
        """
        enclave = self._get_test_enclave()
        self.assertIsInstance(enclave, Enclave)

        self.assertIsNotNone(enclave.edi_service, 'cannot find EDI service')
        url = enclave.edi_service.public_url
        self.assertIsNotNone(url)

        client = RemoteEdiClient(url, token=VARIABLES['DEX_TOKEN'])
        info = client.info()
        self.assertIsInstance(info, dict)


if __name__ == '__main__':
    unittest2.main()
>>>>>>> [#849] sync files with Refactoring:legion/tests/e2e/python/test_k8s_introspection.py
