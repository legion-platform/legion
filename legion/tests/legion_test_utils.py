from argparse import Namespace
import logging
import time
import tempfile
import os
import tarfile
import io
import glob
import subprocess
from unittest.mock import patch

import docker
import docker.types
import docker.errors

import legion.config
import legion.containers.docker
import legion.containers.headers
from legion.model import ModelClient
import legion.model.client
import legion.serving.pyserve as pyserve
from legion.utils import remove_directory

LOGGER = logging.getLogger(__name__)
TEST_MODELS_LOCATION = os.path.join(os.path.dirname(__file__), 'test_models')


def build_distribution():
    """
    Build new version of distribution

    :return: None
    """
    package_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    setup_py_script = os.path.join(package_directory, 'setup.py')

    if not os.path.exists(setup_py_script):
        raise Exception('Cannot find setup.py in a package root: {}'.format(package_directory))

    command = 'python setup.py bdist_wheel'

    LOGGER.info('Executing {!r} in {}..'.format(command, package_directory))
    completed_process = subprocess.run(command, cwd=package_directory, shell=True)

    LOGGER.info('Process returned {}'.format(completed_process.returncode))
    if completed_process.returncode != 0:
        raise Exception('Cannot build distribution: code {} has been returned'
                        .format(completed_process.returncode))


def get_latest_distribution():
    """
    Get path to latest distribution file

    :return: str -- path to file
    """
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist'))
    if not os.path.exists(dist_dir):
        raise Exception('Cannot find dist dir: %s' % dist_dir)

    list_of_files = glob.glob('%s/*.whl' % (dist_dir,))
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def patch_environ(values, flush_existence=False):
    """
    Patch environment with values

    :param values: new values
    :type values: dict[str, str]
    :param flush_existence: flush (clear before overwrite) or not
    :type flush_existence: bool
    :return: unittest2.mock.patch result
    """
    if flush_existence:
        new_values = values
    else:
        new_values = os.environ.copy()
        new_values.update(values)

    return patch('os.environ', new_values)


class LegionTestContainer:
    """
    Context manager for docker containers execution
    """

    def __init__(self, image, port):
        """
        Create context

        :param image: The image name to start container from
        :type image: str
        :param port: Container port to be exposed to the host system
        :type port: int
        """

        self._docker_client = legion.containers.docker.build_docker_client(None)
        self._image = image
        self._port = port

        self.container = None
        self.container_id = None
        self.host_port = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """

        try:
            self.container = self._docker_client.containers.run(self._image,
                                                                ports={self._port: 0},
                                                                detach=True,
                                                                remove=True)
            self.container_id = self.container.id

            wait = 3
            LOGGER.info('Waiting {} sec'.format(wait))
            time.sleep(wait)

            self.container = self._docker_client.containers.get(self.container_id)
            if self.container.status != 'running':
                raise Exception('Invalid container state: {}'.format(self.container.status))

            try:
                self.host_port = self.container.attrs['NetworkSettings']['Ports']['{}/tcp'.format(
                    self._port)][0]['HostPort']
            except Exception as err:
                raise Exception('Error while trying to get exposed container port: {}'.format(err))

        except docker.errors.ContainerError:
            raise Exception('Error creating container from {} image'.format(self._image))

        return self

    def __exit__(self, *args, exception=None):
        """
        Exit from context with container cleanup

        :param args: list of arguments
        :return: None
        """
        if self.container:
            try:
                try:
                    LOGGER.info('Wiping {} container'.format(self.container_id))
                    self.container.kill()
                except Exception as container_kill_exception:
                    LOGGER.info('Can\'t kill container: {}'.format(container_kill_exception))
            except Exception as removing_exception:
                LOGGER.exception('Can\'t remove container: {}'.format(removing_exception),
                                 exc_info=removing_exception)


def print_docker_container_logs(container):
    """
    Print docker container logs to stdout

    :param container: docker container
    :type container: :py:class:`docker.models.containers.Container`
    :return: None
    """
    try:
        logs = container.logs().decode('utf-8')
        print('--- CONTAINER LOGS ---')
        print(logs)
    except Exception as container_log_access_exception:
        print('Cannot get logs of container: {}'.format(container_log_access_exception))


def is_environ_should_be_passed(environ_name):
    """
    Is environ for tests? (should be copied)

    :param environ_name: environ name
    :type environ_name: str
    :return: bool -- should be copied or not
    """
    return environ_name.startswith('PYDEVD_') or environ_name == 'VERBOSE'


def build_environ_for_test_environments():
    """
    Build dict with environ variables that can be used in tests

    :return: dict[str, str] -- environment variables
    """
    new_environ = {
        key: value for (key, value) in os.environ.items()
        if is_environ_should_be_passed(key)
    }

    return new_environ


class ModelDockerBuilderContainerContext:
    def __init__(self,
                 python_wheel_path=None):
        # Base python Docker image
        self._docker_image_version = os.environ.get('BASE_IMAGE_VERSION', 'latest')
        self._docker_tag = 'legion/base-python-image:{}'.format(self._docker_image_version)
        self._docker_base_image = None
        self._docker_container = None
        self._docker_client = legion.containers.docker.build_docker_client(None)

        # Legion python package
        self._python_wheel_path = python_wheel_path
        if not self._python_wheel_path:
            self._python_wheel_path = get_latest_distribution()

    def _prepare_base_docker_container(self):
        """
        Run docker container in which model run will be executed

        :return: None
        """
        try:
            self._docker_base_image = self._docker_client.images.get(self._docker_tag)
        except docker.errors.ImageNotFound:
            raise Exception('Cannot find base docker image with tag {}'.format(self._docker_tag))

        LOGGER.info('Docker image has been selected: {}, starting...'.format(self._docker_base_image))

        docker_socket_mount = docker.types.Mount('/var/run/docker.sock', '/var/run/docker.sock', 'bind')

        self._docker_container = self._docker_client.containers.run(
            self._docker_base_image.id,
            command='sleep 99999',  # keep container running for 99999 seconds
            detach=True,  # in the background
            remove=True,  # remove automatically after kill
            environment=build_environ_for_test_environments(),  # pass required environment variables from host machine
            network_mode='host',  # host network is required because we need to connect to pydevd server
            mounts=[docker_socket_mount]
        )

    def _setup_legion_wheel_in_docker_container(self):
        """
        Copy and install latest Legion wheel (should be prepared with `python setup.py bdist_wheel`)

        :return: None
        """
        filename = os.path.basename(self._python_wheel_path)
        self.copy_file(self._python_wheel_path, '/{}'.format(filename))

        command = 'pip3 install /{}'.format(filename)
        self.exec(command)

    def _shutdown_docker_container(self):
        """
        Shutdown docker container. It will be automatically removed (because of the flags)

        :return: None
        """
        if self._docker_container:
            try:
                LOGGER.info('Killing container')
                self._docker_container.kill()
            except Exception as container_kill_exception:
                LOGGER.info('Cannot kill container: {}'.format(container_kill_exception))

    def __enter__(self):
        try:
            self._prepare_base_docker_container()
            self._setup_legion_wheel_in_docker_container()
        except Exception as container_prepare_exception:
            self._shutdown_docker_container()
            print_docker_container_logs(self._docker_container)
            LOGGER.exception('Cannot start container', exc_info=container_prepare_exception)
            raise

        return self

    def exec(self, command, workdir=None):
        """
        Execute command in container and check exit code

        :param command: command
        :type command: str
        :param workdir: working directory
        :type workdir: str
        :return: str -- output of command
        """

        target_command = 'sh -c \'{}\''.format(command)
        if workdir:
            target_command = 'sh -c \'cd "{}" && {}\''.format(workdir, command)

        LOGGER.info('Executing command {!r}'.format(target_command))
        exitcode, output = self._docker_container.exec_run(target_command)
        output = output.decode('utf-8')
        LOGGER.info('Process returned code: {}'.format(exitcode))
        LOGGER.info(output)

        if exitcode != 0:
            raise Exception('Wrong exitcode {} after executing command {!r}: \n{}'
                            .format(exitcode, target_command, output))

        return output

    def copy_file(self, source, target):
        """
        Copy file from host machine to docker container

        :param source: path on host machine
        :param target: path in docker container (directory should exist)
        :return: None
        """
        LOGGER.info('Copying file {} from host to {} in container'.format(source, target))
        if not os.path.isfile(source):
            raise Exception('{} should be file'.format(source))

        directory, file = os.path.dirname(target), os.path.basename(target)

        tarfile_buffer = io.BytesIO()
        tar = tarfile.open(mode='w', fileobj=tarfile_buffer)
        tar.add(source, arcname=file)
        tar.close()
        tarfile_buffer.seek(0)

        self._docker_container.put_archive(directory, tarfile_buffer)

    def copy_directory(self, source, target):
        """
        Copy directory from host machine to docker container

        :param source: path on host machine
        :param target: path in docker container (parent directory should exist)
        :return: None
        """
        LOGGER.info('Copying directory {} from host to {} in container'.format(source, target))
        if not os.path.isdir(source):
            raise Exception('{} should be directory'.format(source))

        parent, directory_name = target.rsplit('/', 1)
        if not parent:
            parent = '/'

        tarfile_buffer = io.BytesIO()
        tar = tarfile.open(mode='w', fileobj=tarfile_buffer)
        tar.add(source, arcname=directory_name)
        tar.close()
        tarfile_buffer.seek(0)

        self._docker_container.put_archive(parent, tarfile_buffer)

    @property
    def workspace(self):
        """
        Get execution workspace

        :return: str -- path to execution workspace
        """
        return '/workspace'

    def copy_model(self, model_name):
        """
        Copy model file to docker container

        :param model_name: name of model file without .py
        :type model_name: str
        :return: None
        """
        path = os.path.join(TEST_MODELS_LOCATION, model_name)
        if not os.path.exists(path):
            raise Exception('Unknown model {!r}. Path not exists: {!r}'.format(model_name, path))

        self.copy_directory(path, self.workspace)

    def execute_model(self, python_file='run.py'):
        """
        Run model training process

        :param python_file: file to execute
        :type python_file: str
        :return: tuple[str, str, str, str] -- model id, model version, model path, output of execution
        """
        command = 'python3 "{}"'.format(python_file)
        output = self.exec(command, workdir=self.workspace)

        model_id = None
        model_version = None
        model_file = None

        for line in output.splitlines():
            if line.startswith(legion.containers.headers.STDERR_PREFIX):
                line = line[len(legion.containers.headers.STDERR_PREFIX):]
                header, value = line.split(':', maxsplit=1)
                if header == legion.containers.headers.MODEL_ID:
                    model_id = value
                elif header == legion.containers.headers.MODEL_VERSION:
                    model_version = value
                elif header == legion.containers.headers.MODEL_PATH:
                    model_file = value

        return model_id, model_version, model_file, output

    def build_model_container(self, binary_model_file):
        """
        Build model container from model binary with legionctl build

        :param binary_model_file: path to binary model file
        :type binary_model_file: str
        :return: tuple[str, str] -- Docker image sha, output of execution
        """
        command = 'legionctl build "{}"'.format(binary_model_file)
        output = self.exec(command, workdir=self.workspace)

        tag = None

        for line in output.splitlines():
            if line.startswith(legion.containers.headers.STDERR_PREFIX):
                line = line[len(legion.containers.headers.STDERR_PREFIX):]
                header, value = line.split(':', maxsplit=1)
                if header == legion.containers.headers.IMAGE_TAG_LOCAL:
                    _, tag = value.split(':')

        return tag, output

    def __exit__(self, exc_type, exc_val, exc_tb):
        print_docker_container_logs(self._docker_container)
        self._shutdown_docker_container()


class ModelServeTestBuild:
    """
    Context manager for building and testing models with pyserve
    """

    def __init__(self, model_id, model_version, model_builder):
        """
        Create context

        :param model_id: id of model (uses for building model and model client)
        :type model_id: str
        :param model_version: version of model (passes to model builder)
        :param model_builder: str
        """
        self._model_id = model_id
        self._model_version = model_version
        self._model_builder = model_builder

        self._temp_directory = tempfile.mkdtemp()
        self._model_path = os.path.join(self._temp_directory, 'temp.model')

        self.application = None
        self.client = None
        self.model_client = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """
        try:
            print('Building model file {} v {}'.format(self._model_id, self._model_version))
            legion.model.reset_context()
            self._model_builder(self._model_id, self._model_version, self._model_path)
            print('Model file has been built')

            print('Creating pyserve')
            additional_environment = {
                legion.config.REGISTER_ON_GRAFANA[0]: 'false',
                legion.config.MODEL_ID[0]: self._model_id,
                legion.config.MODEL_FILE[0]: self._model_path
            }
            with patch_environ(additional_environment):
                self.application = pyserve.init_application(None)
                self.application.testing = True
                self.client = self.application.test_client()
                self.model_client = legion.model.ModelClient(self._model_id,
                                                             self._model_version,
                                                             http_client=self.client,
                                                             use_relative_url=True)

            return self
        except Exception as build_exception:
            self.__exit__(exception=build_exception)

    def __exit__(self, *args, exception=None):
        """
        Exit from context with cleaning fs temp directory, temporary container and image

        :param args: list of arguements
        :return: None
        """
        print('Removing temporary directory')
        remove_directory(self._temp_directory)

        if exception:
            raise exception


class ModelLocalContainerExecutionContext:
    """
    Context manager for building and testing models
    Hides build and deploy process and provides model client
    """

    def __init__(self, model_image):
        """
        Create context

        :param model_image: docker image id
        :type model_image: str
        """
        self._image_id = model_image
        self._docker_client = legion.containers.docker.build_docker_client(None)

        self._image = self._docker_client.images.get(self._image_id)

        self._model_id = self._image.labels[legion.containers.headers.DOMAIN_MODEL_ID]
        self._model_version = self._image.labels[legion.containers.headers.DOMAIN_MODEL_VERSION]

        self.container = None
        self.container_id = None
        self.model_port = None
        self.client = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """
        try:
            LOGGER.info('Deploying model {} v {} from image {}'.format(self._model_id,
                                                                       self._model_version,
                                                                       self._image_id))

            additional_environment = {
                **build_environ_for_test_environments()
            }

            container_labels = legion.containers.docker.generate_docker_labels_for_container(self._image)

            ports = {'{}/tcp'.format(os.getenv(*legion.config.LEGION_PORT)): 0}

            self.container = self._docker_client.containers.run(self._image_id,
                                                                stdout=True,
                                                                stderr=True,
                                                                detach=True,  # in the background
                                                                remove=True,  # remove automatically after kill
                                                                environment=additional_environment,
                                                                labels=container_labels,
                                                                ports=ports)
            self.container_id = self.container.id

            LOGGER.info('Model image has been deployed')

            wait = 3
            LOGGER.info('Waiting {} sec'.format(wait))
            time.sleep(wait)

            self.container = self._docker_client.containers.get(self.container_id)
            if self.container.status != 'running':
                print_docker_container_logs(self.container)
                raise Exception('Invalid container state: {}'.format(self.container.status))

            LOGGER.info('OK')

            LOGGER.info('Detecting bound ports')
            ports_information = [item for sublist in self.container.attrs['NetworkSettings']['Ports'].values()
                                 for item in sublist]
            ports_information = [int(x['HostPort']) for x in ports_information]
            LOGGER.info('Detected ports: {}'.format(', '.join(str(port) for port in ports_information)))

            if len(ports_information) != 1:
                raise Exception('Should be only one bound port')
            self.model_port = ports_information[0]
            LOGGER.info('Model port: {}'.format(self.model_port))

            LOGGER.info('Building client')
            url = 'http://{}:{}'.format('localhost', self.model_port)
            LOGGER.info('Target URI is {}'.format(url))
            self.client = ModelClient(self._model_id, self._model_version, url)

            LOGGER.info('Getting model information')
            self.model_information = self.client.info()

            return self
        except Exception as build_exception:
            self.__exit__(build_exception)

    def __exit__(self, *args):
        """
        Exit from context with cleaning fs temp directory, temporary container and image

        :param args: list of arguements
        :return: None
        """
        if self.container:
            try:
                LOGGER.info('Finding container')
                container = self._docker_client.containers.get(self.container.id)
                print_docker_container_logs(container)

                try:
                    LOGGER.info('Killing container')
                    container.kill()
                except Exception as container_kill_exception:
                    LOGGER.info('Cannot kill container: {}'.format(container_kill_exception))
            except Exception as removing_exception:
                LOGGER.exception('Cannot remove container: {}'.format(removing_exception),
                                 exc_info=removing_exception)

        if args[0]:
            raise args[0]
