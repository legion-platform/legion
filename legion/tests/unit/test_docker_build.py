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
import logging
import os
import sys
from contextlib import suppress
from time import sleep
from unittest import mock
from unittest.mock import patch

import docker
from docker.errors import ImageNotFound
import unittest2

from legion.sdk.containers.docker import ModelBuildParameters
from legion.sdk.containers.headers import DOMAIN_MODEL_ID, DOMAIN_MODEL_VERSION, DOMAIN_CONTAINER_TYPE
from legion.sdk.clients.docker import request_to_build_image

sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import mock_swagger_function_response_from_file as m_func, DockerBuildServer

DOCKER_IMAGE_LABELS = {
    'com.epam.legion.model.id': 'demo-abc-model',
    'com.epam.legion.model.version': '1.0'
}


def _generate_build_params() -> ModelBuildParameters:
    model_id = 'model-123'
    model_version = '1.0'
    local_image_tag = 'test-model:123'

    return ModelBuildParameters(
        model_id=model_id,
        workspace_path='/home',
        image_labels={
            DOMAIN_MODEL_ID: model_id,
            DOMAIN_MODEL_VERSION: model_version,
            DOMAIN_CONTAINER_TYPE: 'model',
        },
        local_image_tag=local_image_tag,
        push_to_registry=None
    )


class TestRemoteDockerBuild(unittest2.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        self._docker_client = docker.from_env()
        self._build_params = _generate_build_params()

        with suppress(ImageNotFound):
            self._docker_client.images.remove('test-model:123')

    def test_remote_build_and_push(self):
        with DockerBuildServer() as server, \
                patch('legion.sdk.containers.docker.commit_image', return_value='python:3.6'), \
                m_func('kubernetes.client.CoreV1Api.read_namespaced_pod', 'model'), \
                mock.patch('legion.sdk.k8s.utils.build_client', return_value=None):
            model_build_result = request_to_build_image(self._build_params, provider=server.http_client)
            self.assertEqual(self._build_params.local_image_tag, model_build_result.image_name)

            # Raise the error if there is not an image
            self._docker_client.images.get(self._build_params.local_image_tag)

    def test_failed_build(self):
        error_msg = "some exception"

        with DockerBuildServer() as server, \
                m_func('kubernetes.client.CoreV1Api.read_namespaced_pod', 'model'), \
                mock.patch('legion.services.build_services._build_model_image', side_effect=Exception(error_msg)), \
                mock.patch('legion.sdk.k8s.utils.build_client', return_value=None):
            with self.assertRaisesRegex(Exception, error_msg):
                request_to_build_image(self._build_params, provider=server.http_client, sleep=1)

    def test_request_timeout(self):
        with DockerBuildServer() as server, \
                m_func('kubernetes.client.CoreV1Api.read_namespaced_pod', 'model'), \
                mock.patch('legion.services.build_services._build_model_image', side_effect=lambda _: sleep(15)), \
                mock.patch('legion.sdk.k8s.utils.build_client', return_value=None):
            with self.assertRaisesRegex(Exception, 'Failed to wait build result'):
                request_to_build_image(self._build_params, provider=server.http_client, sleep=1, retries=5)


if __name__ == '__main__':
    unittest2.main()
