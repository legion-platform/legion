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
import logging
import os
import stat

import click
from legion.sdk import config, utils

BUILD_TYPE_DOCKER_SOCKET = 'docker-socket'
BUILD_TYPE_DOCKER_REMOTE = 'docker-remote'

LOGGER = logging.getLogger(__name__)


@click.command()
@click.option('--image',
              type=str,
              default=config.SANDBOX_PYTHON_TOOLCHAIN_IMAGE,
              help='explicitly set toolchain python image')
def sandbox(image: str):
    """
    Create the script which allows starting a Jupyterlab instance with Legion plugin as a docker container.\n
    Example of usage:\n
        * Create script: legionctl sandbox --image legion/jupyterlab:latest\n
        * Start Jupyterlab instance: ./legion-activate.sh\n
    Your current directory will be mount to the docker container.
    \f
    :param image: Jupyterlab image
    """
    work_directory = '/work-directory'

    local_fs_work_directory = os.path.abspath(os.getcwd())

    legion_data_directory = '/opt/legion/'
    model_file = 'model.bin'

    arguments = dict(
        local_fs=local_fs_work_directory,
        image=image,
        work_directory=work_directory,
        legion_data_directory=legion_data_directory,
        model_file=model_file,
        remove_arguments='--rm' if config.SANDBOX_CREATE_SELF_REMOVING_CONTAINER else '',
        docker_socket_path=config.SANDBOX_DOCKER_MOUNT_PATH
    )
    cmd = utils.render_template('sandbox-cli.sh.tmpl', arguments)

    path_to_activate = os.path.abspath(os.path.join(os.getcwd(), 'legion-activate.sh'))

    with open(path_to_activate, 'w') as activate_file:
        activate_file.write(cmd)

    current_mode = os.stat(path_to_activate)
    os.chmod(path_to_activate, current_mode.st_mode | stat.S_IEXEC)

    print('Sandbox has been created!')
    print('To activate run {!r} from command line'.format(path_to_activate))
