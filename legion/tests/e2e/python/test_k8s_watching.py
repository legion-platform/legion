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

import logging
import warnings
from contextlib import suppress

import kubernetes
import kubernetes.client.models.v1_namespace
import kubernetes.client.models.v1_object_meta
import unittest2
from nose.plugins.attrib import attr

from legion.robot import profiler_loader
from legion.robot.utils import wait_until, ContextThread
from legion.sdk.definitions import EVENT_DELETED, EVENT_MODIFIED, EVENT_ADDED, ENCLAVE_NAMESPACE_LABEL
from legion.services.k8s import utils as k8s_utils
from legion.services.k8s.enclave import Enclave

warnings.simplefilter('ignore', ResourceWarning)
VARIABLES = profiler_loader.get_variables()

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

        k8s_utils.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(k8s_utils.CONNECTION_CONTEXT))

        with suppress(Exception):
            Enclave(TEST_ENCLAVE_NAME).delete()

    @classmethod
    def tearDownClass(cls):
        with suppress(Exception):
            Enclave(TEST_ENCLAVE_NAME).delete()

    @attr('k8s', 'watch', 'apps')
    def test_watch_enclaves(self):
        """
        Check enclave watching

        :return: None
        """
        events = set()

        def listener():
            for event, enclave in Enclave.watch_enclaves():
                LOGGER.info('Got new event: type={}, enclave={}'.format(event, enclave))
                events.add((event, enclave.name))

        current_namespace_name = VARIABLES['ENCLAVES'][0]

        with ContextThread(listener):
            LOGGER.debug('Waiting before updating')
            self.assertTrue(
                wait_until(lambda: (EVENT_ADDED, current_namespace_name) in events),
                'enclave {!r} has not been added'.format(current_namespace_name)
            )

            client = k8s_utils.build_client()
            core_api = kubernetes.client.CoreV1Api(client)
            current_namespace = core_api.read_namespace(current_namespace_name)

            # Build new namespace specification
            new_namespace_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
                name=TEST_ENCLAVE_NAME, labels={
                    ENCLAVE_NAMESPACE_LABEL: TEST_ENCLAVE_NAME
                })
            new_namespace = kubernetes.client.models.v1_namespace.V1Namespace(
                spec=current_namespace.spec, metadata=new_namespace_metadata)

            # Create new namespace from specification
            core_api.create_namespace(new_namespace)
            self.assertTrue(
                wait_until(lambda: (EVENT_ADDED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been added'.format(TEST_ENCLAVE_NAME)
            )

            # Delete new namespace
            Enclave(TEST_ENCLAVE_NAME).delete(5)
            self.assertTrue(
                wait_until(lambda: (EVENT_MODIFIED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been modified'.format(TEST_ENCLAVE_NAME)
            )
            self.assertTrue(
                wait_until(lambda: (EVENT_DELETED, TEST_ENCLAVE_NAME) in events),
                'enclave {!r} has not been deleted'.format(TEST_ENCLAVE_NAME)
            )


if __name__ == '__main__':
    unittest2.main()
