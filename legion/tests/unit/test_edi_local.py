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
import logging
import sys
import responses

import unittest2
from legion.sdk.clients.edi import LocalEdiClient

from legion.sdk.containers.definitions import ModelDeploymentDescription, ModelBuildInformation
from legion.sdk.containers.docker import build_docker_client

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import \
    add_response_from_file

# Next function could be used for catching responses (should replace responses.activate)
# -> activate_http_api_json_calls_catcher


DOCKER_INSPECT_API_CALL = '/containers/json?limit=-1&all=0&size=0&trunc_cmd=0'
DOCKER_LIST_IMAGES_API_CALL = '/images/json?only_ids=0&all=0&filters=%' + \
                              '7B%22label%22%3A+%5B%22com.epam.legion.model.name%22%5D%7D'

MODEL_A_ID = 'test-math'
MODEL_A_VERSION = '1.0'
MODEL_A_IMAGE = '50d4b8ffcbea59707422d862fe5fea018f6387df2094925241e41ee3846e04b9'
MODEL_A_IMAGE_REF = 'legion-model-test-math:1.0.190206145904.root.0000'
MODEL_A_CONTAINER = '3ab2137c44bb1442c4fb4214c98ec6e7d6df99e8b9710d2cc465fd4f221f1429'
MODEL_A_INFO_URL = 'http://localhost:32768/api/model/test-math/1.0/info'
MODEL_A_DEPLOYMENT_DESCRIPTION = ModelDeploymentDescription(
    'ok',
    'test-math-deployment',
    'test-math',
    '1.0',
    'legion-model-test-math:1.0.190206145904.root.0000',
    1,
    1,
    'local',
    None,
    '3ab2137c44bb1442c4fb4214c98ec6e7d6df99e8b9710d2cc465fd4f221f1429',
    32768,
    True,
    {
        'result': {
            'endpoints': {
                'mul': {'input_params': False, 'name': 'mul', 'use_df': False},
                'sum': {'input_params': False, 'name': 'sum', 'use_df': False}
            },
            'model_name': 'test-math', 'model_version': '1.0'
        }
    }
)

MODEL_B_ID = 'test-math'
MODEL_B_VERSION = '1.1'
MODEL_B_IMAGE = 'c10216153fa6dee020dfa2c0a6df96b0cdec9fb0cc406b036c35b66ae5c8d2a7'
MODEL_B_IMAGE_REF = 'legion-model-test-math:1.0.190206145335.root.0000'
MODEL_B_CONTAINER = '00d32111629cdbc809084b7d711b1ce6b457dbf9000e3a1a3b83f38423945d05'
MODEL_B_INFO_URL = 'http://localhost:32768/api/model/test-math/1.1/info'
MODEL_B_DEPLOYMENT_DESCRIPTION = ModelDeploymentDescription(
    'ok',
    'test-math-deployment-2',
    'test-math',
    '1.1',
    'legion-model-test-math:1.0.190206145335.root.0000',
    1,
    1,
    'local',
    None,
    '00d32111629cdbc809084b7d711b1ce6b457dbf9000e3a1a3b83f38423945d05',
    32771,
    True,
    {
        'result': {
            'endpoints': {
                'mul': {'input_params': False, 'name': 'mul', 'use_df': False},
                'sum': {'input_params': False, 'name': 'sum', 'use_df': False}
            },
            'model_name': 'test-math', 'model_version': '1.1'
        }
    }
)

IMAGE_C_ID = 'sha256:2dc048c72ef9d2480fcd8e9f95d7ad66e87abcacd314966654c3e48ea11aadd1'
IMAGE_D_ID = 'sha256:a4d8852b0d8a7c2d3df01fa74527675a0d583eae44aa62f827dd052ccc241882'


class TestEDILocal(unittest2.TestCase):
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.client = LocalEdiClient()
        self.docker_api_client = build_docker_client()
        self.prefix = self.docker_api_client.api._url('')

    def _register_no_models_inspect(self):
        add_response_from_file(self.prefix + DOCKER_INSPECT_API_CALL,
                               'local_deploy_docker_list_empty')

    def _register_model_a_info(self):
        add_response_from_file(self.prefix + '/containers/{}/json'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_info')

        add_response_from_file(self.prefix + '/images/{}/json'.format(MODEL_A_IMAGE),
                               'local_deploy_docker_image_a_info')

        add_response_from_file(MODEL_A_INFO_URL,
                               'local_deploy_model_a_info')

        add_response_from_file(self.prefix + '/images/{}/json'.format(MODEL_A_IMAGE),
                               'local_deploy_docker_image_a_info')

    def _register_model_a_inspect(self):
        add_response_from_file(self.prefix + DOCKER_INSPECT_API_CALL,
                               'local_deploy_docker_list_one_a')
        self._register_model_a_info()

    def _register_model_b_info(self):
        add_response_from_file(self.prefix + '/containers/{}/json'.format(MODEL_B_CONTAINER),
                               'local_deploy_docker_container_b_info')

        add_response_from_file(self.prefix + '/images/{}/json'.format(MODEL_B_IMAGE),
                               'local_deploy_docker_image_b_info')

        add_response_from_file(MODEL_B_INFO_URL,
                               'local_deploy_model_b_info')

        add_response_from_file(self.prefix + '/images/{}/json'.format(MODEL_B_IMAGE),
                               'local_deploy_docker_image_b_info')

    def _register_model_b_inspect(self):
        add_response_from_file(self.prefix + DOCKER_INSPECT_API_CALL,
                               'local_deploy_docker_list_one_b')
        self._register_model_b_info()

    def _register_model_a_and_b_inspect(self):
        add_response_from_file(self.prefix + DOCKER_INSPECT_API_CALL,
                               'local_deploy_docker_list_a_b')
        self._register_model_a_info()
        self._register_model_b_info()

    def _register_model_a_deploy(self):
        add_response_from_file(self.prefix + '/images/{}/json'.format(MODEL_A_IMAGE_REF),
                               'local_deploy_docker_image_a_info')

        add_response_from_file(self.prefix + DOCKER_INSPECT_API_CALL,
                               'local_deploy_docker_list_empty')

        add_response_from_file(self.prefix + '/containers/create',
                               'local_deploy_docker_image_a_create',
                               responses.POST)

        add_response_from_file(self.prefix + '/containers/{}/json'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_info')

        add_response_from_file(self.prefix + '/containers/{}/start'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_start',
                               responses.POST)

    def _register_image_set(self):
        add_response_from_file(self.prefix + DOCKER_LIST_IMAGES_API_CALL,
                               'local_deploy_docker_image_set')

        add_response_from_file(self.prefix + '/images/{}/json'.format(IMAGE_C_ID),
                               'local_deploy_docker_image_c_info')

        add_response_from_file(self.prefix + '/images/{}/json'.format(IMAGE_D_ID),
                               'local_deploy_docker_image_d_info')


class TestEDILocalInspect(TestEDILocal):

    @responses.activate
    def test_inspect_empty(self):
        self._register_no_models_inspect()

        items = self.client.inspect()
        self.assertListEqual(items, [])

    @responses.activate
    def test_inspect_one_a_alive(self):
        self._register_model_a_inspect()

        items = self.client.inspect()
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_b_alive(self):
        self._register_model_b_inspect()

        items = self.client.inspect()
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_B_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_two_a_b_alive(self):
        self._register_model_a_and_b_inspect()

        items = self.client.inspect()
        self.assertEqual(len(items), 2, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)
        self.assertEqual(items[1], MODEL_B_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_alive_model_name_correct(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model=MODEL_A_ID)
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_alive_model_name_asterisk(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model='*')
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_alive_model_name_incorrect(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model=MODEL_A_ID + '_incorrect')
        self.assertListEqual(items, [])

    @responses.activate
    def test_inspect_one_alive_model_name_version_correct(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model=MODEL_A_ID, version=MODEL_A_VERSION)
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_alive_model_name_version_asterisk(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model=MODEL_A_ID, version='*')
        self.assertEqual(len(items), 1, 'could not find one model')
        self.assertEqual(items[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_inspect_one_alive_model_name_version_incorrect(self):
        self._register_model_a_inspect()

        items = self.client.inspect(model=MODEL_A_ID, version=MODEL_A_VERSION + '_incorrect')
        self.assertListEqual(items, [])


class TestEDILocalDeploy(TestEDILocal):
    @responses.activate
    def test_deploy_on_empty(self):
        self._register_no_models_inspect()

        self._register_model_a_deploy()

        self._register_model_a_inspect()

        items = self.client.inspect()
        self.assertListEqual(items, [])

        affected_models = self.client.deploy(deployment_name='test-math-deployment', image=MODEL_A_IMAGE_REF)
        self.assertEqual(len(affected_models), 1, 'could not find one model')
        self.assertEqual(affected_models[0], MODEL_A_DEPLOYMENT_DESCRIPTION)


class TestEDILocalListBuilds(TestEDILocal):
    @responses.activate
    def test_list_builds(self):
        self._register_image_set()

        items = self.client.get_builds()
        self.assertEqual(len(items), 2, 'count of detected images is incorrect')
        self.assertListEqual(items, [
            ModelBuildInformation(image_name='legion-model-test-summation:1.0.190517145902.root.0000',
                                  model_name='test-summation', model_version='1.0'),
            ModelBuildInformation(image_name='sha256:a4d8852b0d', model_name='test-summation', model_version='1.0')
        ])


class TestEDILocalUndeploy(TestEDILocal):
    @responses.activate
    def test_undeploy_on_empty(self):
        self._register_no_models_inspect()

        with self.assertRaises(Exception) as exc_info:
            self.client.undeploy(model=MODEL_A_ID)

        self.assertTupleEqual(exc_info.exception.args, ('No one model can be found',))

    @responses.activate
    def test_undeploy_correct(self):
        self._register_model_a_inspect()

        add_response_from_file(self.prefix + '/containers/{}/stop'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_stop',
                               responses.POST)

        affected_models = self.client.undeploy(model=MODEL_A_ID)
        self.assertEqual(len(affected_models), 1, 'could not find one model')
        self.assertEqual(affected_models[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_undeploy_correct_with_filter(self):
        self._register_model_a_and_b_inspect()

        add_response_from_file(self.prefix + '/containers/{}/stop'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_stop',
                               responses.POST)

        affected_models = self.client.undeploy(model=MODEL_A_ID, version=MODEL_A_VERSION)
        self.assertEqual(len(affected_models), 1, 'could not find one model')
        self.assertEqual(affected_models[0], MODEL_A_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_undeploy_correct_with_asterisk(self):
        self._register_model_a_and_b_inspect()

        add_response_from_file(self.prefix + '/containers/{}/stop'.format(MODEL_A_CONTAINER),
                               'local_deploy_docker_container_a_stop',
                               responses.POST)

        add_response_from_file(self.prefix + '/containers/{}/stop'.format(MODEL_B_CONTAINER),
                               'local_deploy_docker_container_a_stop',
                               responses.POST)

        affected_models = self.client.undeploy(model=MODEL_A_ID, version='*')
        self.assertEqual(len(affected_models), 2, 'could not find one model')
        self.assertEqual(affected_models[0], MODEL_A_DEPLOYMENT_DESCRIPTION)
        self.assertEqual(affected_models[1], MODEL_B_DEPLOYMENT_DESCRIPTION)

    @responses.activate
    def test_undeploy_correct_without_filter(self):
        self._register_model_a_and_b_inspect()

        with self.assertRaises(Exception) as exc_info:
            self.client.undeploy(model=MODEL_A_ID)

        self.assertTupleEqual(exc_info.exception.args, ('Please specify version of model',))

    @responses.activate
    def test_undeploy_incorrect_id_filter(self):
        self._register_model_a_inspect()

        with self.assertRaises(Exception) as exc_info:
            self.client.undeploy(model=MODEL_A_ID + '_incorrect')

        self.assertTupleEqual(exc_info.exception.args, ('No one model can be found',))

    @responses.activate
    def test_undeploy_incorrect_id_version_filter(self):
        self._register_model_a_inspect()

        with self.assertRaises(Exception) as exc_info:
            self.client.undeploy(model=MODEL_A_ID, version=MODEL_A_VERSION + '_incorrect')

        self.assertTupleEqual(exc_info.exception.args, ('No one model can be found',))


if __name__ == '__main__':
    unittest2.main()
