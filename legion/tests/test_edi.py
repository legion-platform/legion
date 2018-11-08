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

import sys
import os
from unittest import mock

import unittest2
import unittest.mock
from werkzeug.datastructures import FileMultiDict

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import patch_environ, ModelServeTestBuild, EDITestServer, \
    mock_swagger_function_response_from_file as m_func, \
    persist_swagger_function_response_to_file as p_func
from legion_test_models import create_simple_summation_model_by_df, \
    create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
    create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
    create_simple_summation_model_lists_with_files_info

import legion.serving.pyserve as pyserve
import legion.k8s.services


class TestEDI(unittest2.TestCase):
    def test_edi_inspect_all_detail(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect()
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 2)
                # Test model #1 fields
                self.assertEqual(models_info[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[0].model, 'demo-abc-model')
                self.assertEqual(models_info[0].version, '1.0')
                self.assertEqual(models_info[0].scale, 1)
                self.assertEqual(models_info[0].ready_replicas, 1)
                self.assertEqual(models_info[0].namespace, 'debug-enclave')
                # Test model #2 fields
                self.assertEqual(models_info[1].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[1].model, 'demo-abc-model')
                self.assertEqual(models_info[1].version, '1.1')
                self.assertEqual(models_info[1].scale, 1)
                self.assertEqual(models_info[1].ready_replicas, 1)
                self.assertEqual(models_info[1].namespace, 'debug-enclave')

    def test_edi_inspect_by_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect('demo-abc-model')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 2)
                # Test model #1 fields
                self.assertEqual(models_info[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[0].model, 'demo-abc-model')
                self.assertEqual(models_info[0].version, '1.0')
                self.assertEqual(models_info[0].scale, 1)
                self.assertEqual(models_info[0].ready_replicas, 1)
                self.assertEqual(models_info[0].namespace, 'debug-enclave')
                # Test model #2 fields
                self.assertEqual(models_info[1].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[1].model, 'demo-abc-model')
                self.assertEqual(models_info[1].version, '1.1')
                self.assertEqual(models_info[1].scale, 1)
                self.assertEqual(models_info[1].ready_replicas, 1)
                self.assertEqual(models_info[1].namespace, 'debug-enclave')

    def test_edi_inspect_by_model_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect(version='1.0')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 1)
                # Test model #1 fields
                self.assertEqual(models_info[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[0].model, 'demo-abc-model')
                self.assertEqual(models_info[0].version, '1.0')
                self.assertEqual(models_info[0].scale, 1)
                self.assertEqual(models_info[0].ready_replicas, 1)
                self.assertEqual(models_info[0].namespace, 'debug-enclave')

    def test_edi_inspect_by_model_id_and_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect('demo-abc-model', '1.0')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 1)
                # Test model #1 fields
                self.assertEqual(models_info[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                self.assertEqual(models_info[0].model, 'demo-abc-model')
                self.assertEqual(models_info[0].version, '1.0')
                self.assertEqual(models_info[0].scale, 1)
                self.assertEqual(models_info[0].ready_replicas, 1)
                self.assertEqual(models_info[0].namespace, 'debug-enclave')

    def test_edi_inspect_return_none_for_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect('fake_model_id')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_inspect_return_none_for_invalid_model_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect(version='fake_version')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_inspect_filter_empty_results(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'):
                models_info = edi.edi_client.inspect('unexisted-model-id')
                # Test count of returned models
                self.assertIsInstance(models_info, list)
                self.assertEqual(len(models_info), 0)

    def test_edi_deploy_one_model(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'):
                    deployments = edi.edi_client.deploy(
                        '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 1)
                    # Check deployed model fields
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_edi_deploy_model_with_scale_1(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'):
                    deployments = edi.edi_client.deploy(
                        '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', 1)
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 1)
                    # Check deployed models fields
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_edi_deploy_model_with_scale_2(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_scaled_to_2'):
                    deployments = edi.edi_client.deploy(
                        '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', 2)
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 1)
                    # Check deployed models fields
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 2)
                    self.assertEqual(deployments[0].ready_replicas, 2)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_negative_edi_deploy_scale_with_0(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model'):
                try:
                    edi.edi_client.deploy(
                        '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a', 0)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Invalid scale parameter: should be greater then 0'")

    def test_edi_undeploy_model_by_id(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model'), \
                     m_func('kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                            'model_deleted'), \
                     m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'):
                    deployments = edi.edi_client.undeploy('demo-abc-model')
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 1)
                    # Check undeployed model fields
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_negative_edi_undeploy_by_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'):
                try:
                    edi.edi_client.undeploy('invalid-id')
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'No one model can be found'")

    def test_edi_scale_up(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'one_model_scaled_to_2'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model_scaled_to_2'):
                deployments = edi.edi_client.scale('demo-abc-model', 2)
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)
                # Check scaled model fields
                self.assertEqual(deployments[0].model, 'demo-abc-model')
                self.assertEqual(deployments[0].version, '1.0')
                self.assertEqual(deployments[0].status, 'ok')
                self.assertEqual(deployments[0].scale, 2)
                self.assertEqual(deployments[0].ready_replicas, 2)
                self.assertEqual(deployments[0].namespace, 'debug-enclave')
                self.assertEqual(deployments[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_edi_scale_down(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model_scaled_to_2'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'one_model_scaled_to_1'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model'):
                deployments = edi.edi_client.scale('demo-abc-model', 1)
                self.assertIsInstance(deployments, list)
                self.assertEqual(len(deployments), 1)
                # Check scaled model fields
                self.assertEqual(deployments[0].model, 'demo-abc-model')
                self.assertEqual(deployments[0].version, '1.0')
                self.assertEqual(deployments[0].status, 'ok')
                self.assertEqual(deployments[0].scale, 1)
                self.assertEqual(deployments[0].ready_replicas, 1)
                self.assertEqual(deployments[0].namespace, 'debug-enclave')
                self.assertEqual(deployments[0].image,
                                 '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')

    def test_negative_edi_scale_to_0(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment', 'one_model_scaled_to_2'):
                try:
                    edi.edi_client.scale('demo-abc-model', 0)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Invalid scale parameter: should be greater then 0'")

    def test_negative_edi_invalid_model_id(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'one_model'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                        'one_model_scaled_to_2'):
                try:
                    edi.edi_client.scale('invalid_id', 1)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'No one model can be found'")

    def test_edi_inspect_all_models_by_version(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'):
                    deployments = edi.edi_client.inspect(model='demo-abc-model', version='*')
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 2)
                    # Validate scaled models
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                    self.assertEqual(deployments[1].model, 'demo-abc-model')
                    self.assertEqual(deployments[1].version, '1.1')
                    self.assertEqual(deployments[1].status, 'ok')
                    self.assertEqual(deployments[1].scale, 1)
                    self.assertEqual(deployments[1].ready_replicas, 1)
                    self.assertEqual(deployments[1].namespace, 'debug-enclave')
                    self.assertEqual(deployments[1].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')

    def test_edi_inspect_all_models_by_id(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'):
                    deployments = edi.edi_client.inspect(model='*')
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 2)
                    # Validate scaled models
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                    self.assertEqual(deployments[1].model, 'demo-abc-model')
                    self.assertEqual(deployments[1].version, '1.1')
                    self.assertEqual(deployments[1].status, 'ok')
                    self.assertEqual(deployments[1].scale, 1)
                    self.assertEqual(deployments[1].ready_replicas, 1)
                    self.assertEqual(deployments[1].namespace, 'debug-enclave')
                    self.assertEqual(deployments[1].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')

    def test_negative_edi_scale_without_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment', 'one_model_scaled_to_2'):
                try:
                    edi.edi_client.scale('demo-abc-model', 2)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Please specify version of model'")

    def test_negative_edi_undeploy_without_version(self):
        with EDITestServer() as edi:
            with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                        'two_models_1_id_and_2_versions'), \
                 m_func('kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                        'model_deleted'):
                try:
                    edi.edi_client.scale('demo-abc-model', 2)
                except Exception as e:
                    self.assertEqual(str(e),
                                     "Got error from server: 'Please specify version of model'")

    def test_edi_undeploy_all_models_by_version(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
                            'last_model_deleted'), \
                     m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'):
                    deployments = edi.edi_client.undeploy(model='demo-abc-model', version='*')
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 2)
                    # Validate deleted models
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 1)
                    self.assertEqual(deployments[0].ready_replicas, 1)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                    self.assertEqual(deployments[1].model, 'demo-abc-model')
                    self.assertEqual(deployments[1].version, '1.1')
                    self.assertEqual(deployments[1].status, 'ok')
                    self.assertEqual(deployments[1].scale, 1)
                    self.assertEqual(deployments[1].ready_replicas, 1)
                    self.assertEqual(deployments[1].namespace, 'debug-enclave')
                    self.assertEqual(deployments[1].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')

    def test_edi_scale_all_models_by_version(self):
        with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
            with EDITestServer() as edi:
                with m_func('kubernetes.client.CoreV1Api.list_namespaced_service', 'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_1_id_and_2_versions'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
                            'last_model_scaled_to_2'), \
                     m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
                            'two_models_scaled_to_2'):
                    deployments = edi.edi_client.scale(model='demo-abc-model', count=2, version='*')
                    # Test count of returned deployments
                    self.assertIsInstance(deployments, list)
                    self.assertEqual(len(deployments), 2)
                    # Validate scaled models
                    self.assertEqual(deployments[0].model, 'demo-abc-model')
                    self.assertEqual(deployments[0].version, '1.0')
                    self.assertEqual(deployments[0].status, 'ok')
                    self.assertEqual(deployments[0].scale, 2)
                    self.assertEqual(deployments[0].ready_replicas, 2)
                    self.assertEqual(deployments[0].namespace, 'debug-enclave')
                    self.assertEqual(deployments[0].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
                    self.assertEqual(deployments[1].model, 'demo-abc-model')
                    self.assertEqual(deployments[1].version, '1.1')
                    self.assertEqual(deployments[1].status, 'ok')
                    self.assertEqual(deployments[1].scale, 2)
                    self.assertEqual(deployments[1].ready_replicas, 2)
                    self.assertEqual(deployments[1].namespace, 'debug-enclave')
                    self.assertEqual(deployments[1].image,
                                     '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')

    # TODO uncomment after https://github.com/legion-platform/legion/pull/553 will be merged
    # def test_edi_scale_all_models_by_id(self):
    #     with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
    #         with EDITestServer() as edi:
    #             with m_func('kubernetes.client.CoreV1Api.list_namespaced_service',
    #                         'two_models_1_id_and_2_versions'), \
    #                  m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
    #                         'two_models_1_id_and_2_versions'), \
    #                  m_func('kubernetes.client.ExtensionsV1beta1Api.patch_namespaced_deployment',
    #                         'last_model_scaled_to_2'), \
    #                  m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
    #                         'two_models_scaled_to_2'):
    #                 deployments = edi.edi_client.scale(model='*', count=2)
    #                 # Test count of returned deployments
    #                 self.assertIsInstance(deployments, list)
    #                 self.assertEqual(len(deployments), 2)
    #                 # Validate scaled models
    #                 self.assertEqual(deployments[0].model, 'demo-abc-model')
    #                 self.assertEqual(deployments[0].version, '1.0')
    #                 self.assertEqual(deployments[0].status, 'ok')
    #                 self.assertEqual(deployments[0].scale, 2)
    #                 self.assertEqual(deployments[0].ready_replicas, 2)
    #                 self.assertEqual(deployments[0].namespace, 'debug-enclave')
    #                 self.assertEqual(deployments[0].image,
    #                                  '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
    #                 self.assertEqual(deployments[1].model, 'demo-abc-model')
    #                 self.assertEqual(deployments[1].version, '1.1')
    #                 self.assertEqual(deployments[1].status, 'ok')
    #                 self.assertEqual(deployments[1].scale, 2)
    #                 self.assertEqual(deployments[1].ready_replicas, 2)
    #                 self.assertEqual(deployments[1].namespace, 'debug-enclave')
    #                 self.assertEqual(deployments[1].image,
    #                                  '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')

    # def test_edi_undeploy_all_models_by_id(self):
    #     with mock.patch('legion.k8s.enclave.Enclave.graphite_service', return_value=None):
    #         with EDITestServer() as edi:
    #             with m_func('kubernetes.client.CoreV1Api.list_namespaced_service',
    #                         'two_models_1_id_and_2_versions'), \
    #                  m_func('kubernetes.client.ExtensionsV1beta1Api.list_namespaced_deployment',
    #                         'two_models_1_id_and_2_versions'), \
    #                  m_func(
    #                      'kubernetes.client.apis.apps_v1beta1_api.AppsV1beta1Api.delete_namespaced_deployment',
    #                      'last_model_deleted'), \
    #                  m_func('kubernetes.client.CoreV1Api.delete_namespaced_service', 'undeploy_done'):
    #                 deployments = edi.edi_client.undeploy(model='*')
    #                 # Test count of returned deployments
    #                 self.assertIsInstance(deployments, list)
    #                 self.assertEqual(len(deployments), 2)
    #                 # Validate deleted models
    #                 self.assertEqual(deployments[0].model, 'demo-abc-model')
    #                 self.assertEqual(deployments[0].version, '1.0')
    #                 self.assertEqual(deployments[0].status, 'ok')
    #                 self.assertEqual(deployments[0].scale, 1)
    #                 self.assertEqual(deployments[0].ready_replicas, 1)
    #                 self.assertEqual(deployments[0].namespace, 'debug-enclave')
    #                 self.assertEqual(deployments[0].image,
    #                                  '127.0.0.1/legion/test-bare-model-api-model-1:0.9.0-20181106123540.560.3b9739a')
    #                 self.assertEqual(deployments[1].model, 'demo-abc-model')
    #                 self.assertEqual(deployments[1].version, '1.1')
    #                 self.assertEqual(deployments[1].status, 'ok')
    #                 self.assertEqual(deployments[1].scale, 1)
    #                 self.assertEqual(deployments[1].ready_replicas, 1)
    #                 self.assertEqual(deployments[1].namespace, 'debug-enclave')
    #                 self.assertEqual(deployments[1].image,
    #                                  '127.0.0.1/legion/test-bare-model-api-model-2:0.9.0-20181106123540.560.3b9739a')


if __name__ == '__main__':
    unittest2.main()
