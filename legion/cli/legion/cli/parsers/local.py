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
Local commands for legion cli
"""
import argparse
import logging
import os
import stat
import uuid

from legion.sdk import config, utils
from legion.sdk.clients.docker import request_to_build_image
from legion.sdk.containers import docker
from legion.sdk.containers.definitions import ModelBuildParameters
from legion.sdk.containers.docker import prepare_build, build_model_docker_image
from legion.sdk.model import load_meta_model

BUILD_TYPE_DOCKER_SOCKET = 'docker-socket'
BUILD_TYPE_DOCKER_REMOTE = 'docker-remote'

LOGGER = logging.getLogger(__name__)


def build_model(args):
    """
    Build model

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    model_file = args.model_file
    if not model_file:
        model_file = config.MODEL_FILE

    if not model_file:
        raise Exception('Model file has not been provided')

    if not os.path.exists(model_file):
        raise Exception('Cannot find model binary {}'.format(model_file))

    container = load_meta_model(model_file)
    model_id = container.model_id
    model_version = container.model_version
    workspace_path = os.getcwd()

    image_labels = docker.generate_docker_labels_for_image(model_file, model_id)
    new_image_tag = args.docker_image_tag
    if not new_image_tag:
        new_image_tag = 'legion-model-{}:{}.{}'.format(model_id, model_version, utils.deduce_extra_version())

    prepare_build(model_id, model_file)

    params = ModelBuildParameters(model_id, workspace_path, image_labels, new_image_tag, args.push_to_registry,
                                  build_id=str(uuid.uuid4()))

    if args.build_type == BUILD_TYPE_DOCKER_SOCKET:
        model_image = build_model_docker_image(params)
    elif args.build_type == BUILD_TYPE_DOCKER_REMOTE:
        model_image = request_to_build_image(params)
    else:
        raise ValueError(f'Unexpected build type: {args.build_type}')

    LOGGER.info('The image %s has been built', model_image)


def sandbox(args):
    """
    Create local sandbox
    It generates bash script to run sandbox


    :param args: command arguments with .image, .force_recreate
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    work_directory = '/work-directory'

    local_fs_work_directory = os.path.abspath(os.getcwd())

    legion_data_directory = '/opt/legion/'
    model_file = 'model.bin'

    arguments = dict(
        local_fs=local_fs_work_directory,
        image=args.image,
        work_directory=work_directory,
        legion_data_directory=legion_data_directory,
        model_file=model_file,
        remove_arguments='--rm' if config.SANDBOX_CREATE_SELF_REMOVING_CONTAINER else '',
        docker_socket_path=config.SANDBOX_DOCKER_MOUNT_PATH
    )
    cmd = utils.render_template('sandbox-cli.sh.tmpl', arguments)

    path_to_activate = os.path.abspath(os.path.join(os.getcwd(), 'legion-activate.sh'))

    if os.path.exists(path_to_activate) and not args.force_recreate:
        print('File {} already existed, ignoring creation of sandbox'.format(path_to_activate))
        return

    with open(path_to_activate, 'w') as activate_file:
        activate_file.write(cmd)

    current_mode = os.stat(path_to_activate)
    os.chmod(path_to_activate, current_mode.st_mode | stat.S_IEXEC)

    print('Sandbox has been created!')
    print('To activate run {!r} from command line'.format(path_to_activate))


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    build_model_parser = main_subparser.add_parser('build',
                                                   description='build model into new docker image (should be run '
                                                               'in the docker container)')
    build_model_parser.add_argument('--model-file',
                                    type=str, help='serialized model file name')
    build_model_parser.add_argument('--docker-image-tag',
                                    type=str, help='docker image tag')
    build_model_parser.add_argument('--push-to-registry',
                                    type=str, help='docker registry address')
    build_model_parser.add_argument('--build-type', default='docker-socket', choices=[BUILD_TYPE_DOCKER_SOCKET,
                                                                                      BUILD_TYPE_DOCKER_REMOTE],
                                    type=str,
                                    help="Available values: docker-socket - builds a model image using a docker socket."
                                         "docker-remote - does not build image yourself. Send an HTTP request to the "
                                         "MODEL_DOCKER_BUILDER_URL server that determines the model container, builds "
                                         "and pushes it.")
    build_model_parser.set_defaults(func=build_model)

    sandbox_parser = main_subparser.add_parser('create-sandbox', description='create sandbox')
    sandbox_parser.add_argument('--image',
                                type=str,
                                default=config.SANDBOX_PYTHON_TOOLCHAIN_IMAGE,
                                help='explicitly set toolchain python image')
    sandbox_parser.add_argument('--force-recreate',
                                action='store_true',
                                help='recreate sandbox if it already existed')
    sandbox_parser.set_defaults(func=sandbox)
