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
import os
import time
import unittest
import unittest.mock

import unittest2

import legion.k8s
import legion.config
import legion.containers.docker
import legion.external
import legion.containers.headers
import legion_test.profiler_loader
import legion_test.test_assets
import legion_test.utils
import legion_test.robot
from nose.plugins.attrib import attr

warnings.simplefilter('ignore', ResourceWarning)

VARIABLES = legion_test.profiler_loader.get_variables()
LOGGER = logging.getLogger(__name__)

TEST_MODEL_ID = 'demo-abc-model'
TEST_MODEL_VERSION = '1.0'
TEST_IMAGE = legion_test.test_assets.get_test_bare_model_api_image(VARIABLES)


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

        legion.k8s.CONNECTION_CONTEXT = VARIABLES['CLUSTER_NAME']
        LOGGER.info('K8S context has been set to {}'.format(legion.k8s.CONNECTION_CONTEXT))

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
                    legion_test.utils.wait_until(lambda: not enclave.get_models(model_id, model_version)),
                    'model service {!r} has not been removed'.format(model_service)
                )
            except Exception as remove_exception:
                logging.error('Cannot remove model service: {}'.format(remove_exception))

    def _get_test_enclave(self):
        """
        Get test enclave object

        :return: :py:class:`legion.k8s.Enclave` -- test enclave
        """
        all_enclaves = legion.k8s.find_enclaves()
        self.assertIsInstance(all_enclaves, list, 'cannot find any enclave')

        enclaves_map = {e.name: e for e in all_enclaves}
        self.assertIn(VARIABLES['MODEL_TEST_ENCLAVE'], enclaves_map, 'cannot find test enclave')
        return enclaves_map[VARIABLES['MODEL_TEST_ENCLAVE']]

    @attr('k8s', 'models')
    def test_bare_model_deploy(self):
        """
        Test bare model deploy

        :return: None
        """
        enclave = self._get_test_enclave()

        self.assertFalse(enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION), 'model already deployed')

        model_service = enclave.deploy_model(TEST_IMAGE)

        self.assertTrue(
            legion_test.utils.wait_until(lambda: enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} not found after deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

        self.assertEqual(model_service.id, TEST_MODEL_ID)
        self.assertEqual(model_service.version, TEST_MODEL_VERSION)

    @attr('k8s', 'models')
    def test_bare_model_deploy_undeploy(self):
        """
        Test bare model deploy

        :return: None
        """
        enclave = self._get_test_enclave()

        self.assertFalse(enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION), 'model already deployed')

        model_service = enclave.deploy_model(TEST_IMAGE)

        self.assertTrue(
            legion_test.utils.wait_until(lambda: enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} not found after deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

        model_service.delete()

        self.assertTrue(
            legion_test.utils.wait_until(lambda: not enclave.get_models(TEST_MODEL_ID, TEST_MODEL_VERSION)),
            'model service for model {} {} found after un deploy'.format(TEST_MODEL_ID, TEST_MODEL_VERSION)
        )

    @attr('k8s', 'models')
    def test_model_watch_service_endpoints_state(self):
        states = []  # history of states (each state consists model services)

        enclave = self._get_test_enclave()

        def listener():
            for new_state in enclave.watch_model_service_endpoints_state():
                states.append(new_state)
                LOGGER.info('Got new model state update: {}'.format(repr(new_state)))

        def is_test_model_in_last_state():
            return states and any(ep.model_service.id == TEST_MODEL_ID for ep in states[-1])

        with legion_test.utils.ContextThread(listener):
            enclave = self._get_test_enclave()
            self.assertFalse(is_test_model_in_last_state(), 'state has been found but model has not been deployed yet')

            model_service = enclave.deploy_model(TEST_IMAGE)
            self.assertTrue(legion_test.utils.wait_until(lambda: is_test_model_in_last_state()),
                            'state has not been found but model has been deployed')

            # Delete new model
            model_service.delete()
            self.assertTrue(legion_test.utils.wait_until(lambda: not is_test_model_in_last_state()),
                            'state has been found but model has been removed')

    @attr('k8s', 'models')
    def test_model_information(self):
        """
        Test that target-test model present

        :return: None
        """
        enclave = self._get_test_enclave()
        model_service = enclave.deploy_model(TEST_IMAGE)

        self.assertIsInstance(model_service.id, str, 'cannot get model id')
        self.assertGreater(len(model_service.id), 0, 'empty model id string')

        self.assertIsInstance(model_service.version, str, 'cannot get model version')
        self.assertGreater(len(model_service.version), 0, 'empty model version string')

        self.assertIsNotNone(model_service.deployment, 'cannot get model deployment')

        self.assertIsInstance(model_service.id_and_version, legion.k8s.ModelIdVersion,
                              'wrong type of model id and version structure')
        self.assertEqual(model_service.id_and_version,
                         legion.k8s.ModelIdVersion(model_service.id, model_service.version),
                         'wrong model id and version value')

        self.assertIsInstance(model_service.scale, int, 'wrong model current scale type')

        legion_test.utils.wait_until(lambda: model_service.reload_cache() or model_service.scale > 0)

        self.assertGreater(model_service.scale, 0, 'wrong model current scale value')
        self.assertIsInstance(model_service.desired_scale, int, 'wrong model current scale type')
        self.assertEqual(model_service.scale, model_service.desired_scale, 'desired and current scales are not equal')

        self.assertEqual(model_service.status, legion.k8s.STATUS_OK, 'wrong model status')

        self.assertIsInstance(model_service.image, str, 'cannot get model image')
        self.assertGreater(len(model_service.image), 0, 'empty model image string')

    @attr('k8s', 'models')
    def test_model_scale_up_and_down(self):
        """
        Test model scale up and scale down procedure

        :return: None
        """
        enclave = self._get_test_enclave()
        model_service = enclave.deploy_model(TEST_IMAGE)

        legion_test.utils.wait_until(lambda: model_service.reload_cache() or model_service.scale > 0)

        self.assertEqual(model_service.scale, model_service.desired_scale, 'desired and current scales are not equal')
        current_scale = model_service.scale

        # Scale up
        new_scale = current_scale + 1
        model_service.scale = new_scale

        model_service.reload_cache()
        self.assertEqual(model_service.desired_scale, new_scale, 'Desired scale has not been set after reload')

        legion_test.utils.wait_until(lambda: model_service.reload_cache()
                                             or model_service.scale == model_service.desired_scale)

        model_service.reload_cache()
        self.assertEqual(model_service.scale, new_scale, 'Model has not been scaled up')

        # Scale down
        new_scale = current_scale
        model_service.scale = new_scale

        model_service.reload_cache()
        self.assertEqual(model_service.desired_scale, new_scale, 'Desired scale has not been set after reload')

        legion_test.utils.wait_until(lambda: model_service.reload_cache()
                                             or model_service.scale == model_service.desired_scale)

        model_service.reload_cache()
        self.assertEqual(model_service.scale, new_scale, 'Model has not been scaled down')


if __name__ == '__main__':
    unittest2.main()
