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
from nose.plugins.attrib import attr


warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = legion_test.profiler_loader.get_variables()

TEST_ENCLAVE_NAME = 'company-x'
LOGGER = logging.getLogger(__name__)


class TestK8SWatching(unittest2.TestCase):
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
            legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete()
        except:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete()
        except:
            pass

    @attr('k8s', 'watch')
    def test_watch_enclaves(self):
        """
        Check enclave watching

        :return: None
        """
        events = set()

        def listener():
            for event, enclave in legion.k8s.Enclave.watch_enclaves():
                LOGGER.info('Got new event: type={}, enclave={}'.format(event, enclave))
                events.add((event, enclave.name))

        current_namespace_name = VARIABLES['ENCLAVES'][0]

        with legion_test.utils.ContextThread(listener):
            LOGGER.debug('Waiting before updating')
            self.assertTrue(
                legion_test.utils.wait_until(lambda: (legion.k8s.EVENT_ADDED, current_namespace_name) in events),
                'enclave {!r} has not been added'.format(current_namespace_name)
            )

            client = legion.k8s.utils.build_client()
            core_api = kubernetes.client.CoreV1Api(client)
            current_namespace = core_api.read_namespace(current_namespace_name)

            # Build new namespace specification
            new_namespace_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
                name=TEST_ENCLAVE_NAME, labels={
                    legion.k8s.definitions.ENCLAVE_NAMESPACE_LABEL: TEST_ENCLAVE_NAME
                })
            new_namespace = kubernetes.client.models.v1_namespace.V1Namespace(
                spec=current_namespace.spec, metadata=new_namespace_metadata)

            # Create new namespace from specification
            core_api.create_namespace(new_namespace)
            self.assertTrue(
                legion_test.utils.wait_until(lambda: (legion.k8s.EVENT_ADDED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been added'.format(TEST_ENCLAVE_NAME)
            )

            # Delete new namespace
            legion.k8s.Enclave(TEST_ENCLAVE_NAME).delete(5)
            self.assertTrue(
                legion_test.utils.wait_until(lambda: (legion.k8s.EVENT_MODIFIED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been modified'.format(TEST_ENCLAVE_NAME)
            )
            self.assertTrue(
                legion_test.utils.wait_until(lambda: (legion.k8s.EVENT_DELETED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been deleted'.format(TEST_ENCLAVE_NAME)
            )


if __name__ == '__main__':
    unittest2.main()
