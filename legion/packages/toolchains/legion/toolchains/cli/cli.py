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
import logging
import argparse

import legion.core
import legion.toolchains.containers


LOGGER = logging.getLogger(__name__)


def build_model(args):
    """
    Build model

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Image` docker image
    """
    client = legion.core.containers.docker.build_docker_client()

    model_file = args.model_file
    if not model_file:
        model_file = legion.core.config.MODEL_FILE

    if not model_file:
        raise Exception('Model file has not been provided')

    if not os.path.exists(model_file):
        raise Exception('Cannot find model binary {}'.format(model_file))

    container = legion.pymodel.Model.load(model_file)
    model_id = container.model_id
    model_version = container.model_version

    image_labels = legion.toolchains.containers.docker.generate_docker_labels_for_image(model_file, model_id)

    LOGGER.info('Building docker image...')

    new_image_tag = args.docker_image_tag
    if not new_image_tag:
        new_image_tag = 'legion-model-{}:{}.{}'.format(model_id, model_version, legion.utils.deduce_extra_version())

    image = legion.core.containers.docker.build_docker_image(
        client,
        model_id,
        model_file,
        image_labels,
        new_image_tag
    )

    LOGGER.info('Image has been built: {}'.format(image))

    legion.core.utils.send_header_to_stderr(legion.core.containers.headers.IMAGE_ID_LOCAL, image.id)

    if image.tags:
        legion.core.utils.send_header_to_stderr(legion.core.containers.headers.IMAGE_TAG_LOCAL, image.tags[0])

    if args.push_to_registry:
        legion.core.containers.docker.push_image_to_registry(client, image, args.push_to_registry)

    return image


if __name__ == '__main__':

    # --------- LOCAL DOCKER SECTION -----------
    build_model_parser = parser.add_parser('build', description='build model into new docker image (should be run '
                                                                    'in the docker container)')
    build_model_parser.add_argument('--model-file',
                                    type=str, help='serialized model file name')
    build_model_parser.add_argument('--docker-image-tag',
                                    type=str, help='docker image tag')
    build_model_parser.add_argument('--push-to-registry',
                                    type=str, help='docker registry address')
    build_model_parser.set_defaults(func=build_model)
