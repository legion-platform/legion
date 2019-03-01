#
#    Copyright 2019 EPAM Systems
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
"""
Remote docker builder client
"""
import json
import logging
import typing

import requests
from requests import RequestException

from legion import config
from legion.containers.definitions import ModelBuildParameters, ModelBuildResult
from legion.containers.server import DOCKER_BUILD_URL
from legion.utils import ensure_function_succeed

LOGGER = logging.getLogger(__name__)


def request_to_build_image(params: ModelBuildParameters, provider: typing.Any = requests, retries: int = 60,
                           sleep: int = 10, http_exception: Exception = RequestException) -> ModelBuildResult:
    """
    Send request to build a model container

    :param retries: number of retries maximum
    :param sleep: sleeping time between iteration
    :param provider: http request provider. It must have the put, data and status_code methods
    :param params: model docker build parameters
    :param http_exception: http_client exception class, which can be thrown by http_client in case of some errors
    :return model docker image
    """
    def check_function() -> typing.Optional[ModelBuildResult]:
        """
        Return mode build result if the model build finishes

        :return: model docker build parameters
        """
        try:
            resp = provider.put(config.MODEL_DOCKER_BUILDER_URL.strip('/') + DOCKER_BUILD_URL,  # pylint: disable=E1101
                                data=json.dumps(params._asdict()), headers={'Content-Type': 'application/json'})

            if not resp.ok:
                LOGGER.error('Got error from server: [status_code=%s, text=%s]', resp.status_code, resp.data)
                return

            model_build_res = ModelBuildResult(**resp.json())

            if not model_build_res.ready:
                LOGGER.debug('Still waiting to finish the build %s', params.build_id)
                return

            if model_build_res.error:
                raise Exception(model_build_res.error)

            return model_build_res
        except http_exception as exception:
            LOGGER.error('Failed to connect to %s: %s.', config.MODEL_DOCKER_BUILDER_URL, exception)

    model_build_result = ensure_function_succeed(check_function, retries, sleep)
    if not model_build_result:
        raise Exception('Failed to wait build result')

    return model_build_result
