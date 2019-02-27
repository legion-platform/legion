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
import os.path
import logging

from unittest import mock
import unittest2

import legion.k8s
import legion.k8s.utils
import legion.config
import legion.containers.docker
import legion.containers.headers
import legion.utils
from legion.k8s.utils import ImageAttributes
from legion.k8s.utils import parse_docker_image_url
from legion.k8s.utils import reduce_cpu_resource
from legion.k8s.utils import reduce_mem_resource

REGISTRY_IMAGE = 'registry:2.6.1'

try:
    from .legion_test_utils import LegionTestContainer
except ImportError:
    from legion_test_utils import LegionTestContainer

LOGGER = logging.getLogger(__name__)


class TestK8S(unittest2.TestCase):
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls):
        cls.data_directory = os.path.join(os.path.dirname(__file__), 'data')
        cls.state = os.path.join(cls.data_directory, 'state.yaml')
        cls.secrets = os.path.join(cls.data_directory, 'secrets')

    def _build_bare_docker_image(self, image_name, labels=None):
        docker_client = legion.containers.docker.build_docker_client()
        new_image = docker_client.images.build(
            tag=image_name,
            nocache=True,
            path=os.path.join(self.data_directory, 'empty-docker'),
            rm=True,
            labels=labels
        )

        return new_image[0]

    def _push_docker_image_to_registry(self, image_name, ref, registry):
        try:
            docker_client = legion.containers.docker.build_docker_client()
            image = docker_client.images.get(image_name)
            image_tag = '{}/{}:{}'.format(registry, image_name, ref)
            LOGGER.info('Pushing {} image to registry'.format(image_tag))
            image.tag(image_tag)
            docker_client.images.push(image_tag)
        except Exception as err:
            print('Can\'t push image {} to registry: {}'.format(image, err))

    @staticmethod
    def _build_test_model_labels(model_id='id', model_version='1.0', container_type='model'):
        return {
            legion.containers.headers.DOMAIN_MODEL_ID: model_id,
            legion.containers.headers.DOMAIN_MODEL_VERSION: model_version,
            legion.containers.headers.DOMAIN_CONTAINER_TYPE: container_type,
        }

    def test_secrets_loading(self):
        secrets = legion.k8s.load_secrets(self.secrets)
        valid = {'grafana.user': 'admin', 'grafana.password': 'test-password'}
        self.assertIsInstance(secrets, dict)
        self.assertDictEqual(secrets, valid)

    def test_cluster_config_loading(self):
        config = legion.k8s.load_config(self.state)
        valid = {'grafana': {'port': 123, 'domain': 'legion-grafana.default.svc.cluster.local'}}
        self.assertIsInstance(config, dict)
        self.assertDictEqual(config, valid)

    @mock.patch('legion.config.DOCKER_REGISTRY_PROTOCOL', 'http')
    def test_get_labels_from_docker_image_exception_on_missed(self):
        with self.assertRaises(Exception) as raised_exception:
            with LegionTestContainer(image=REGISTRY_IMAGE, port=5000) as registry_container:
                labels = self._build_test_model_labels()
                del labels[legion.containers.headers.DOMAIN_MODEL_VERSION]
                image_name = 'legion/test-image'
                image_ref = '1.0-180713070916.1.bad661d'
                self._build_bare_docker_image(image_name, labels)
                registry_url = 'localhost:{}'.format(registry_container.host_port)

                self._push_docker_image_to_registry(image_name, image_ref, registry_url)
                image_url = 'localhost:{}/{}:{}'.format(registry_container.host_port, image_name, image_ref)
                legion.k8s.utils.get_docker_image_labels(image_url)
        self.assertEqual(len(raised_exception.exception.args), 1, 'exception doesn\'t contain arguments')
        self.assertTrue(raised_exception.exception.args[0].startswith('Missed one of '), 'wrong exception text')

    @mock.patch('legion.config.DOCKER_REGISTRY_PROTOCOL', 'http')
    def test_get_labels_from_docker_image_exception(self):
        with LegionTestContainer(image=REGISTRY_IMAGE, port=5000) as registry_container:
            labels = self._build_test_model_labels()
            image_name = 'legion/test-image'
            image_ref = '1.0-123'
            self._build_bare_docker_image(image_name, labels)
            self._push_docker_image_to_registry(
                image_name=image_name,
                ref=image_ref,
                registry='localhost:{}'.format(registry_container.host_port)
            )
            image_url = 'localhost:{}/{}:{}'.format(registry_container.host_port, image_name, image_ref)
            received_labels = legion.k8s.utils.get_docker_image_labels(image_url)
            self.assertDictEqual(received_labels, labels)

    def test_get_meta_from_docker_labels(self):
        source_model_id = 'abc'
        source_model_version = '1.2'

        labels = self._build_test_model_labels(source_model_id, source_model_version)
        image_meta_information = legion.k8s.utils.get_meta_from_docker_labels(labels)

        self.assertEqual(image_meta_information.model_id, source_model_id)
        self.assertEqual(image_meta_information.model_version, source_model_version)

        expected_k8s_name = legion.utils.normalize_name('model-{}-{}'.format(image_meta_information.model_id,
                                                                             image_meta_information.model_version),
                                                        dns_1035=True)
        self.assertEqual(image_meta_information.k8s_name, expected_k8s_name)

        self.assertIsInstance(image_meta_information.kubernetes_labels, dict, 'labels is not a dict')
        self.assertTrue(image_meta_information.kubernetes_labels, 'empty labels')
        for key, value in image_meta_information.kubernetes_labels.items():
            self.assertIsInstance(key, str, 'labels key is not a string')
            self.assertIsInstance(value, str, 'labels key is not a string')

        self.assertIsInstance(image_meta_information.kubernetes_annotations, dict, 'annotations is not a dict')
        self.assertTrue(image_meta_information.kubernetes_annotations, 'empty annotations')
        for key, value in image_meta_information.kubernetes_annotations.items():
            self.assertIsInstance(key, str, 'annotations key is not a string')
            self.assertIsInstance(value, str, 'annotations key is not a string')

    def test_container_id_detection_kubernetes(self):
        self.assertEqual(legion.containers.docker.get_docker_container_id_from_cgroup_line(
            '9:perf_event:/kubepods/burstable/pod9aa3c2f1-8381-11e8-9508-0ae20568e616' +
            '/8383095d66a50d724da34073b512a468ee565042586a4a7a5bbc741aa426e012'
        ), '8383095d66a50d724da34073b512a468ee565042586a4a7a5bbc741aa426e012')

    def test_container_id_detection_docker(self):
        self.assertEqual(legion.containers.docker.get_docker_container_id_from_cgroup_line(
            '9:devices:/docker/54d998b5f4232277ef245f7d93b0156dec3e149186916c557190983863bc7f57'
        ), '54d998b5f4232277ef245f7d93b0156dec3e149186916c557190983863bc7f57')

    def test_parse_docker_image_url(self):
        image_attributes = parse_docker_image_url(
            'nexus.example.com/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4')
        self.assertEqual(ImageAttributes(
            host='nexus.example.com', repo='legion-test-null-test-summation', ref='1.0-190115092855.1.56ed5f4'
        ), image_attributes)

        image_attributes = parse_docker_image_url(
            'nexus.example.com:443/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4')
        self.assertEqual(ImageAttributes(
            host='nexus.example.com:443', repo='legion-test-null-test-summation',
            ref='1.0-190115092855.1.56ed5f4'
        ), image_attributes)

        image_attributes = parse_docker_image_url(
            'nexus.example.com/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4')
        self.assertEqual(ImageAttributes(
            host='nexus.example.com', repo='legion/test-bare-model-api-model-6',
            ref='0.10.0-20190115075121.273.56ed5f4'
        ), image_attributes)

        image_attributes = parse_docker_image_url(
            'nexus.example.com:443/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4')
        self.assertEqual(ImageAttributes(
            host='nexus.example.com:443', repo='legion/test-bare-model-api-model-6',
            ref='0.10.0-20190115075121.273.56ed5f4'
        ), image_attributes)

    def test_mem_resource_reducer(self):
        self.assertEqual(reduce_mem_resource('256Mi'), '171Mi')
        self.assertEqual(reduce_mem_resource('3G'), '2058Mi')
        self.assertEqual(reduce_mem_resource('1G'), '686Mi')
        self.assertEqual(reduce_mem_resource('333'), '223')

        for res in '300Mi123', '300sdsd', '', 'sdsd':
            with self.assertRaisesRegex(ValueError, 'Malformed mem resource'):
                reduce_mem_resource(res)

    def test_cpu_resource_reducer(self):
        self.assertEqual(reduce_cpu_resource('256m'), '171m')
        self.assertEqual(reduce_cpu_resource('3'), '2010m')
        self.assertEqual(reduce_cpu_resource('1'), '670m')
        self.assertEqual(reduce_cpu_resource('333m'), '223m')

        for res in '300m123', '300sdsd', '', 'sdsd':
            with self.assertRaisesRegex(ValueError, 'Malformed cpu resource'):
                reduce_cpu_resource(res)


if __name__ == '__main__':
    unittest2.main()
