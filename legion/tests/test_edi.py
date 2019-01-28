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
from unittest import mock

import unittest2

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import EDITestServer, \
    mock_swagger_function_response_from_file as m_func

from kubernetes.client.rest import ApiException

DOCKER_IMAGE_LABELS = {
    'com.epam.legion.model.id': 'demo-abc-model',
    'com.epam.legion.model.version': '1.0'
}


class TestEDI(unittest2.TestCase):
    _multiprocess_can_split_ = True

    def test_edi_inspect_all_detail(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_1']), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect()
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 2)
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[0].image,
                    'model': models_info[0].model,
                    'version': models_info[0].version,
                    'scale': models_info[0].scale,
                    'ready_replicas': models_info[0].ready_replicas,
                    'namespace': models_info[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[1].image,
                    'model': models_info[1].model,
                    'version': models_info[1].version,
                    'scale': models_info[1].scale,
                    'ready_replicas': models_info[1].ready_replicas,
                    'namespace': models_info[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_inspect_by_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_1']), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect('demo-abc-model')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 2)
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[0].image,
                    'model': models_info[0].model,
                    'version': models_info[0].version,
                    'scale': models_info[0].scale,
                    'ready_replicas': models_info[0].ready_replicas,
                    'namespace': models_info[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[1].image,
                    'model': models_info[1].model,
                    'version': models_info[1].version,
                    'scale': models_info[1].scale,
                    'ready_replicas': models_info[1].ready_replicas,
                    'namespace': models_info[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_inspect_by_model_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment', 'demo_abc_model_1_0'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect(version='1.0')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 1)
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[0].image,
                    'model': models_info[0].model,
                    'version': models_info[0].version,
                    'scale': models_info[0].scale,
                    'ready_replicas': models_info[0].ready_replicas,
                    'namespace': models_info[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_inspect_by_model_id_and_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment', 'demo_abc_model_1_0'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect('demo-abc-model', '1.0')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 1)
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': models_info[0].image,
                    'model': models_info[0].model,
                    'version': models_info[0].version,
                    'scale': models_info[0].scale,
                    'ready_replicas': models_info[0].ready_replicas,
                    'namespace': models_info[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_inspect_return_none_for_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'no_models'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect('fake_model_id')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_inspect_return_none_for_invalid_model_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'no_models'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'demo_abc_models_1_0_and_1_1'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect(version='fake_version')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_inspect_filter_empty_results(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'no_models'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'demo_abc_models_1_0_and_1_1'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                models_info = edi.edi_client.inspect('unexisted-model-id')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_deploy_one_model(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), 'demo_abc_model_1_0']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.create_namespaced_deployment', 'deploy_done'), \
                 m_func('kubernetes.client.CoreV1Api.create_namespaced_service', 'deploy_done'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None), \
                 mock.patch('legion.k8s.utils.get_docker_image_labels', return_value=DOCKER_IMAGE_LABELS):
                deployments = edi.edi_client.deploy(
                    '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)
                # Check deployed model fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_deploy_model_with_scale_1(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), 'demo_abc_model_1_0']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.create_namespaced_deployment',
                        'deploy_done') as cnd_mock, \
                 m_func('kubernetes.client.CoreV1Api.create_namespaced_service', 'deploy_done'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None), \
                 mock.patch('legion.k8s.utils.get_docker_image_labels', return_value=DOCKER_IMAGE_LABELS):
                deployments = edi.edi_client.deploy(
                    '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', count=1)
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)

                _, deployment_spec = cnd_mock.call_args
                self.assertEqual(1, deployment_spec['body'].spec.replicas)

                # Check deployed models fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_deploy_model_with_scale_2(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), 'demo_abc_model_1_0']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        'demo_abc_model_1_0_scaled_to_2'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.create_namespaced_deployment',
                        'deploy_done') as cnd_mock, \
                 m_func('kubernetes.client.CoreV1Api.create_namespaced_service', 'deploy_done'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None), \
                 mock.patch('legion.k8s.utils.get_docker_image_labels', return_value=DOCKER_IMAGE_LABELS):
                deployments = edi.edi_client.deploy(
                    '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', count=2)
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)

                _, deployment_spec = cnd_mock.call_args
                self.assertEqual(2, deployment_spec['body'].spec.replicas)

                # Check deployed models fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_negative_edi_deploy_scale_with_0(self):
        with EDITestServer() as edi:
            with mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.deploy(
                        '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', count=0)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Invalid scale parameter: should be greater then 0'")

    def test_edi_undeploy_model_by_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.CoreV1Api.read_namespaced_service', ApiException(404)), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', ApiException(404)]), \
                 m_func('kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                        'model_deleted'), \
                 m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.undeploy('demo-abc-model')
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)
                # Check undeployed model fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_negative_edi_undeploy_by_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'no_models'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.undeploy('invalid-id')
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'No one model can be found'")

    def test_edi_scale_up(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_0_scaled_to_2']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'demo_abc_model_1_0_scaled_to_2') as pnd_mock, \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                deployments = edi.edi_client.scale('demo-abc-model', 2)
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)

                _, _, deployment_spec = pnd_mock.call_args[0]
                self.assertEqual(2, deployment_spec.spec.replicas)

                # Check scaled model fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_scale_down(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0_scaled_to_2', 'demo_abc_model_1_0']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'demo_abc_model_1_0_scaled_to_1') as pnd_mock, \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                deployments = edi.edi_client.scale('demo-abc-model', 1)
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)

                _, _, deployment_spec = pnd_mock.call_args[0]
                self.assertEqual(1, deployment_spec.spec.replicas)

                # Check scaled model fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_negative_edi_scale_to_0(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_model_1_0'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment', 'demo_abc_model_1_0'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.scale('demo-abc-model', 0)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Invalid scale parameter: should be greater then 0'")

    def test_negative_edi_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'no_models'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.scale('invalid_id', 1)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'No one model can be found'")

    def test_edi_inspect_all_models_by_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_1']), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.inspect(model='demo-abc-model', version='*')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)
                # Validate scaled models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_inspect_all_models_by_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_1']), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.inspect(model='*')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)
                # Validate scaled models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_negative_edi_scale_without_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.scale('demo-abc-model', 2)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Please specify version of model'")

    def test_negative_edi_undeploy_without_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None):
                try:
                    edi.edi_client.scale('demo-abc-model', 2)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Please specify version of model'")

    def test_edi_undeploy_all_models_by_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), ApiException(404)]), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', ApiException(404),
                         'demo_abc_model_1_1', ApiException(404)]), \
                 m_func('kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                        'last_model_deleted'), \
                 m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'), \
                 mock.patch('legion.k8s.utils.is_code_run_in_cluster', return_value=None), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.undeploy(model='demo-abc-model', version='*')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)
                # Validate deleted models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_scale_all_models_by_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), ApiException(404)]), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_0_scaled_to_2',
                         'demo_abc_model_1_1', 'demo_abc_model_1_1_scaled_to_2']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'last_model_scaled_to_2') as pnd_mock, \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.scale(model='demo-abc-model', count=2, version='*')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)

                for args in pnd_mock.call_args_list:
                    _, _, deployment_spec = args[0]
                    self.assertEqual(2, deployment_spec.spec.replicas)

                # Validate scaled models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_scale_all_models_by_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), ApiException(404)]), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', 'demo_abc_model_1_0_scaled_to_2',
                         'demo_abc_model_1_1', 'demo_abc_model_1_1_scaled_to_2']), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'last_model_scaled_to_2') as pnd_mock, \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.scale(model='*', count=2)
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)

                for args in pnd_mock.call_args_list:
                    _, _, deployment_spec = args[0]
                    self.assertEqual(2, deployment_spec.spec.replicas)

                # Validate scaled models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }

                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 2,
                    'ready_replicas': 2,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)

    def test_edi_undeploy_all_models_by_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'demo_abc_models_1_0_and_1_1'), \
                 m_func('kubernetes.client.CoreV1Api.read_namespaced_service',
                        [ApiException(404), ApiException(404)]), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.read_namespaced_deployment',
                        ['demo_abc_model_1_0', ApiException(404),
                         'demo_abc_model_1_1', ApiException(404)]), \
                 m_func(
                     'kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                     'last_model_deleted'), \
                 m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'), \
                 mock.patch('legion.k8s.utils.build_client', return_value=None), \
                 mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
                deployments = edi.edi_client.undeploy(model='*')
                # Test count of returned deployments
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 2)
                # Validate deleted models
                # Test model #1 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.0',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[0].image,
                    'model': deployments[0].model,
                    'version': deployments[0].version,
                    'scale': deployments[0].scale,
                    'ready_replicas': deployments[0].ready_replicas,
                    'status': deployments[0].status,
                    'namespace': deployments[0].namespace
                }
                self.assertDictEqual(expected_result, actual_result)
                # Test model #2 fields
                expected_result = {
                    'image': '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a',
                    'model': 'demo-abc-model',
                    'version': '1.1',
                    'scale': 1,
                    'ready_replicas': 1,
                    'status': 'ok',
                    'namespace': 'debug-enclave'
                }
                actual_result = {
                    'image': deployments[1].image,
                    'model': deployments[1].model,
                    'version': deployments[1].version,
                    'scale': deployments[1].scale,
                    'ready_replicas': deployments[1].ready_replicas,
                    'status': deployments[1].status,
                    'namespace': deployments[1].namespace
                }
                self.assertDictEqual(expected_result, actual_result)


if __name__ == '__main__':
    unittest2.main()
