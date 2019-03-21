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
Flask model docker service
"""
import logging
import typing
from concurrent.futures import Future, ThreadPoolExecutor

from flask import Flask, Blueprint, request
from flask import current_app as app

from legion.sdk.containers.definitions import ModelBuildParameters, ModelBuildResult
from legion.sdk.containers.docker import build_model_docker_image
from legion.sdk.definitions import DOCKER_BUILD_URL
from legion.services.k8s.utils import get_container_id_of_current_pod
from legion.sdk.logging import set_log_level, redirect_to_stdout
from legion.services.edi.http import provide_json_response

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('docker_server', __name__)

MODEL_CONTAINER_NAME = 'model'
BUILD_POOL = 'BUILD_POOL'
BUILD_FUTURES = 'BUILD_FUTURES'


def _build_model_image(params: ModelBuildParameters) -> str:
    """
    Commit and build model container

    :param params: Model build parameters
    :return: built image name
    """
    model_container_id = get_container_id_of_current_pod(MODEL_CONTAINER_NAME)

    return build_model_docker_image(params, model_container_id)


@blueprint.route(DOCKER_BUILD_URL, methods=['PUT'])
@provide_json_response
def build() -> ModelBuildResult:
    """
    Build model image API endpoint

    :return: build id
    """
    params = ModelBuildParameters(**request.get_json(force=True))
    futures: typing.Dict[str, Future] = app.config[BUILD_FUTURES]

    future: Future = futures.get(params.build_id)

    if not future:
        futures[params.build_id] = app.config[BUILD_POOL].submit(_build_model_image, params)

        return ModelBuildResult(ready=False)

    if future.done():
        error = future.exception()

        if error:
            return ModelBuildResult(ready=True, error=str(error))
        else:
            return ModelBuildResult(ready=True, image_name=future.result())
    else:
        return ModelBuildResult(ready=False)


def init_application() -> Flask:
    """
    Initialize Flask application instance

    :return: Flask application instance
    """
    set_log_level()
    redirect_to_stdout()

    flask_app = Flask(__name__)
    flask_app.register_blueprint(blueprint)

    flask_app.config[BUILD_POOL] = ThreadPoolExecutor(max_workers=1)
    flask_app.config[BUILD_FUTURES] = {}

    return flask_app
