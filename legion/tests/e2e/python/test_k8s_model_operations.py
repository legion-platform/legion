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
import os
import warnings

from nose.plugins.attrib import attr
import unittest2

from legion.robot import profiler_loader
from legion.robot.libraries import k8s
from legion.robot.utils import wait_until, ContextThread
from legion.services.k8s import utils as k8s_utils
from legion.services.k8s.enclave import find_enclaves

warnings.simplefilter('ignore', ResourceWarning)

VARIABLES = profiler_loader.get_variables()
LOGGER = logging.getLogger(__name__)

TEST_MODEL_ID = 'demo-abc-model'
TEST_MODEL_VERSION = '1'
TEST_IMAGE = None


class TestK8SModelOperations(unittest2.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enclave = None
        self.data_directory = os.path.join(os.path.dirname(__file__), 'data')
        LOGGER.info('Using image {} for tests'.format(TEST_IMAGE))

    def setUp(self):
        self._remove_model_if_exists(TEST_MODEL_ID)

    def tearDown(self):
        self._remove_model_if_exists(TEST_MODEL_ID)

    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context and run Jenkins job

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

        k8s_utils.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(k8s_utils.CONNECTION_CONTEXT))

        status_cr = k8s.K8s(VARIABLES['MODEL_TEST_ENCLAVE']).build_stub_model(TEST_MODEL_ID, TEST_MODEL_VERSION)
        global TEST_IMAGE
        TEST_IMAGE = status_cr["modelImage"]

    @classmethod
    def tearDownClass(cls):
        k8s.K8s(VARIABLES['MODEL_TEST_ENCLAVE']).delete_stub_model_training(TEST_MODEL_ID, TEST_MODEL_VERSION)

    def _remove_model_if_exists(self, model_id, model_version=None):
        """
        Remove model if exists

        :param model_id: model ID
        :type model_id: str
        :param model_version: (Optional) model version
        :type model_version: str
        :return: None
        """
        enclave = self._get_test_enclave()
        model_services = enclave.get_models(model_id, model_version)

        for model_service in model_services:
            try:
                logging.info('Removing {!r}'.format(model_service))
                model_service.delete()
                self.assertTrue(
                    wait_until(lambda: not enclave.get_models(model_id, model_version)),
                    'model service {!r} has not been removed'.format(model_service)
                )
            except Exception as remove_exception:
                logging.error('Cannot remove model service: {}'.format(remove_exception))

    def _get_test_enclave(self):
        """
        Get test enclave object

        :return: :py:class:`legion.k8s.Enclave` -- test enclave
        """
        all_enclaves = find_enclaves()
        self.assertIsInstance(all_enclaves, list, 'cannot find any enclave')

        enclaves_map = {e.name: e for e in all_enclaves}
        self.assertIn(VARIABLES['MODEL_TEST_ENCLAVE'], enclaves_map, 'cannot find test enclave')
        return enclaves_map[VARIABLES['MODEL_TEST_ENCLAVE']]

    @attr('k8s', 'models', 'apps')
    def test_bare_model_deploy(self):
        """
        Test bare model deploy

        :return: None
        """
        enclave = self._get_test_enclave()

        self.assertFalse(enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION), 'model already deployed')

        is_deployed, model_service = enclave.deploy_model(TEST_IMAGE)

        self.assertTrue(is_deployed, 'model already deployed')
        self.assertTrue(
            wait_until(lambda: enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} not found after deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

        self.assertEqual(model_service.id, TEST_MODEL_ID)
        self.assertEqual(model_service.version, TEST_MODEL_VERSION)

    @attr('k8s', 'models', 'apps')
    def test_bare_model_deploy_undeploy(self):
        """
        Test bare model deploy

        :return: None
        """
        enclave = self._get_test_enclave()

        self.assertFalse(enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION), 'model already deployed')

        is_deployed, model_service = enclave.deploy_model(TEST_IMAGE)

        self.assertTrue(is_deployed, 'model already deployed')
        self.assertTrue(
            wait_until(lambda: enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} not found after deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

        model_service.delete()

        self.assertTrue(
            wait_until(lambda: not enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} found after un deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

    @attr('k8s', 'models', 'apps')
    def test_model_watch_service_endpoints_state(self):
        states = []  # history of states (each state consists model services)

        enclave = self._get_test_enclave()

        def listener():
            for new_state, _ in enclave.watch_model_service_endpoints_state():
                states.append(new_state)
                LOGGER.info('Got new model state update: {}'.format(repr(new_state)))

        def is_test_model_in_last_state():
            return states and any(ep.model_service.id == TEST_MODEL_ID for ep in states[-1])

        with ContextThread(listener):
            enclave = self._get_test_enclave()
            self.assertFalse(is_test_model_in_last_state(), 'state has been found but model has not been deployed yet')

            is_deployed, model_service = enclave.deploy_model(TEST_IMAGE)

            self.assertTrue(is_deployed, 'model already deployed')
            self.assertTrue(wait_until(is_test_model_in_last_state),
                            'state has not been found but model has been deployed')

            # Delete new model
            model_service.delete()
            self.assertTrue(wait_until(lambda: not is_test_model_in_last_state()),
                            'state has been found but model has been removed')


if __name__ == '__main__':
    unittest2.main()
