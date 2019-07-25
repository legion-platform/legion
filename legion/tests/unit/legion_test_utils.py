# pylint: disable=C0302
import contextlib
import glob
import importlib
import inspect
import io
import json
import logging
import os
import pty
import re
import subprocess
import tarfile
import tempfile
import time
import typing
from unittest.mock import patch

import docker
import docker.client
import docker.errors
import docker.types
import requests
import requests.adapters
import responses

from legion.sdk import config
from legion.sdk.clients.model import ModelClient
from legion.sdk.containers import headers
from legion.sdk.containers.docker import build_docker_client, generate_docker_labels_for_container
from legion.sdk.utils import remove_directory, ensure_function_succeed
from legion.toolchain import model
from legion.toolchain.server import pyserve

LOGGER = logging.getLogger(__name__)
TEST_MODELS_LOCATION = os.path.join(os.path.dirname(__file__), 'test_models')
TEST_DATA_LOCATION = os.path.join(os.path.dirname(__file__), 'data')
TEST_RESPONSES_LOCATION = os.path.join(TEST_DATA_LOCATION, 'responses')

ResponseObjectType = typing.NamedTuple('ResponseObjectType', [
    ('data', object)
])


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


@contextlib.contextmanager
def multi_context(*cms):
    """
    Build multiple context managers

    :param cms: context managers
    :return: None
    """
    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(cls()) for cls in cms]


@contextlib.contextmanager
def patch_config(new_config):
    """
    Patch configuration

    :param new_config: new configuration values
    :type new_config: dict[str, str]
    :return: None
    """
    contexts = [
        patch('legion.sdk.config.' + key, new_value) for (key, new_value) in new_config.items()
    ]
    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(inst) for inst in contexts]


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


def build_sequential_resource_name_generator(responses_list):
    """
    Build function that can sequential return name of responses

    :param responses_list: list of responses
    :type responses_list: list[str]
    :return: Callable[[], str] -- function that generates name of responses
    """
    i = 0

    def func():
        nonlocal i
        if i >= len(responses_list):
            raise Exception('Function is called #{} time, but have only {} variant(s)'.format(
                i + 1, len(responses_list)
            ))
        value = responses_list[i]
        i += 1
        return value

    return func


def print_stack_trace(stack_state):
    """
    Print stack trace info to console

    :param stack_state: stack trace frames
    :type stack_state: litst[]
    """
    for frame in stack_state:
        print('* function {} {}:{}'.format(frame.function, frame.filename, frame.lineno))


@contextlib.contextmanager
def persist_swagger_function_response_to_file(function, test_resource_name):
    """
    Context managers
    Persist result of invocation swagger client query data to disk

    :param function: name of function
    :type function: str
    :param test_resource_name: name of test response (is used in file naming), e.g. two_models OR
                               function that returns this string
    :type test_resource_name: str or Callable[[], str]
    """
    client = build_swagger_function_client(function)
    origin = client.__class__.deserialize

    def response_catcher(self, response, type_name):
        _1, function_name = function.rsplit('.', maxsplit=1)
        call_stack = inspect.stack()
        call_stack_functions = [f.function for f in call_stack]

        if function_name in call_stack_functions:
            print('Trying to persist function {}'.format(function))
            # Very verbose test debugging:
            # print_stack_trace(call_stack[:-2])

            if callable(test_resource_name):
                current_test_resource_name = test_resource_name()
            elif isinstance(test_resource_name, str):
                current_test_resource_name = test_resource_name
            else:
                raise Exception('Invalid type of argument ({}). Should be callable or string')
            path = '{}/{}.{}.{}.json'.format(TEST_RESPONSES_LOCATION, function,
                                             type_name, current_test_resource_name)

            print('Persisting to resource {} ({})'.format(current_test_resource_name, path))
            with open(path, 'w') as stream:
                data = json.loads(response.data)
                json.dump(data, stream, indent=2, sort_keys=True)

        return origin(self, response, type_name)

    client.__class__.deserialize = response_catcher
    yield
    client.__class__.deserialize = origin


def build_swagger_function_client(function):
    """
    Build swagger client for function

    :param function: name of function to mock, e.g. kubernetes.client.CoreV1Api.list_namespaced_service
    :type function: str
    :return: object -- generated swagger API client
    """

    module_name, module_class, _1 = function.rsplit('.', maxsplit=2)
    module_instance = importlib.import_module(module_name)
    module_api_client_class = getattr(module_instance, module_class)
    module_api_client = module_api_client_class()
    return module_api_client.api_client


def mock_swagger_function_response_from_file(function, test_resource_name):
    """
    Mock swagger client function with response from file

    :param function: name of function to mock, e.g. kubernetes.client.CoreV1Api.list_namespaced_service
    :type function: str or BaseException
    :param test_resource_name: name of test response (is used in file naming), e.g. two_models OR
                               function that returns this string
    :type test_resource_name: str or Callable[[], str or BaseException]
    :return: Any -- response
    """
    if isinstance(test_resource_name, list):
        test_resource_name = build_sequential_resource_name_generator(test_resource_name)

    def response_catcher(*args, **kwargs):  # pylint: disable=W0613
        print('Trying to return mocked answer for {}'.format(function))
        # Very verbose test debugging:
        # call_stack = inspect.stack()
        # print_stack_trace(call_stack[:-2])

        if callable(test_resource_name):
            current_test_resource_name = test_resource_name()
        elif isinstance(test_resource_name, (str, BaseException)):
            current_test_resource_name = test_resource_name
        else:
            raise Exception('Invalid type of argument ({}). Should be callable or string')

        # This helps to emulate kubernetes exception
        if isinstance(current_test_resource_name, BaseException):
            raise current_test_resource_name  # pylint: disable=E0702

        searched_files = glob.glob('{}/{}.*.{}.json'.format(TEST_RESPONSES_LOCATION, function,
                                                            current_test_resource_name))

        if not searched_files:
            raise Exception('Cannot find response example file for function {!r} with code {!r}'.format(
                function, current_test_resource_name
            ))

        if len(searched_files) > 1:
            raise Exception('Finded more then one file for function {!r} with code {!r}'.format(
                function, current_test_resource_name
            ))

        path, filename = searched_files[0], os.path.basename(searched_files[0])
        splits = filename.rsplit('.')
        return_type = splits[-3]
        print('Trying to return mocked answer for {} using {}'.format(function, path))

        client = build_swagger_function_client(function)

        with open(path) as response_file:
            data = ResponseObjectType(data=response_file.read())

        return client.deserialize(data, return_type)

    return patch(function, side_effect=response_catcher)


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

        self._docker_client = build_docker_client()
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


class ManagedProcessContext:
    """
    Context manager for start and control process with stdout / stderr as a file streams
    """

    STREAM_DEBUG_SLICE = 1024

    def __init__(self, *args, streams_location=None, **kwargs):
        self._streams_location = streams_location
        self._process = None

        self._args = args
        self._kwargs = kwargs

        self._read_stdout_callback = None
        self._read_stdout_finished_mark = 0
        self._read_stderr_callback = None
        self._read_stderr_finished_mark = 0

        self._last_stdin_command = None
        self._stdin_buffer = ''

        self._pty_master, self._pty_slave = None, None

        self._streams_finished_mark = None

    def _prepare_stream(self, stream_name, args_holder):
        if stream_name not in self._kwargs:
            stream_folder = self._streams_location
            if not stream_folder:
                stream_folder = os.getcwd()
            stream_file = os.path.join(stream_folder, stream_name)

            if os.path.exists(stream_file):
                print('Overwriting file {!r}'.format(stream_name))

            stream = open(stream_file, 'w')
            args_holder[stream_name] = stream

            def read_callback():
                with open(stream_file, 'r') as read_stream:
                    return read_stream.read()

            setattr(self, '_read_{}_callback'.format(stream_name), read_callback)

    def _start_process(self):
        args = self._args[:]
        kwargs = self._kwargs.copy()

        self._prepare_stream('stdout', kwargs)
        self._prepare_stream('stderr', kwargs)
        if 'stdin' not in kwargs:
            self._pty_master, self._pty_slave = pty.openpty()
            kwargs['stdin'] = self._pty_slave
            kwargs['preexec_fn'] = os.setsid
            kwargs['close_fds'] = True

        self._process = subprocess.Popen(*args, **kwargs)
        if self._pty_slave:
            os.close(self._pty_slave)

    def mark_streams_finished(self):
        self._streams_finished_mark = self._calculate_all_streams_hash()
        self._read_stdout_finished_mark = len(self.stdout)
        self._read_stderr_finished_mark = len(self.stderr)

    def wait_streams_changed(self, retries=4, timeout=1):
        def check_function():
            current_mark = self._calculate_all_streams_hash()
            return current_mark != self._streams_finished_mark

        data = ensure_function_succeed(check_function, retries, timeout, boolean_check=True)
        if not data:
            raise Exception('There are no updates in streams')
        return True

    def get_stream_changed_data(self, stream_name='stdout'):
        current_data = getattr(self, stream_name)
        if not current_data:
            return ''

        old_mark = getattr(self, '_read_{}_finished_mark'.format(stream_name))

        return current_data[old_mark:]

    def _calculate_stream_hash(self, stream_name):
        return hash(getattr(self, stream_name))

    def _calculate_all_streams_hash(self):
        return self._calculate_stream_hash('stdout') + self._calculate_stream_hash('stderr')

    @property
    def process(self):
        return self._process

    @property
    def stdout(self):
        if self._read_stdout_callback and callable(self._read_stdout_callback):
            return self._read_stdout_callback()  # pylint: disable=E1102

        return self.process.stdout

    @property
    def stderr(self):
        if self._read_stderr_callback and callable(self._read_stderr_callback):
            return self._read_stderr_callback()  # pylint: disable=E1102

        return self.process.stderr

    def wait_stream_output(self, needle_string_pattern, stream='stdout', retries=60, timeout=5):
        regex_patter = re.compile(needle_string_pattern)
        ending = ''

        def check_function():
            nonlocal ending
            lines = getattr(self, stream)
            if not lines or not isinstance(lines, str):
                return None

            ending = lines[-ManagedProcessContext.STREAM_DEBUG_SLICE:]

            lines = lines.splitlines(False)
            last_line = lines[-1]
            if regex_patter.findall(last_line):
                return last_line
            else:
                return None

        data = ensure_function_succeed(check_function, retries, timeout)
        if not data:
            raise Exception('There is no {!r} text in stream {!r}. Ending: {!r}'.format(
                needle_string_pattern, stream, ending
            ))
        return data

    def write_to_stdin(self, message, end='\n'):
        if self._pty_master:
            command = self._last_stdin_command = message + end
            self._stdin_buffer += command
            os.write(self._pty_master, command.encode('utf-8'))

    @property
    def last_stdin_command(self):
        return self._last_stdin_command if self._last_stdin_command else ''

    def debug_output(self):
        stdout = self.stdout
        stderr = self.stderr
        if stdout and isinstance(stdout, str):
            print('------\nSTDOUT of container: \n{}'.format(
                stdout[-ManagedProcessContext.STREAM_DEBUG_SLICE:]
            ))
        if stderr and isinstance(stderr, str):
            print('------\nSTDERR of container: \n{}'.format(
                stderr[-ManagedProcessContext.STREAM_DEBUG_SLICE:]
            ))
        if self._stdin_buffer:
            print('------\nSTDIN of container: \n{}'.format(
                self._stdin_buffer[-ManagedProcessContext.STREAM_DEBUG_SLICE:]
            ))

    def __enter__(self):
        self._start_process()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            self.debug_output()
            if self._pty_master:
                os.write(self._pty_master, b'\004\004')  # send Ctrl-D x2
            self._process.kill()


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


@contextlib.contextmanager
def gather_stdout_stderr():
    """
    Context manager that temporarily redirects stdout/stderr to StringIO buffers

    :return: (io.StringIO, io.StringIO) -- temporarily buffers
    """
    stdout, stderr = io.StringIO(), io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        yield stdout, stderr


def is_environ_should_be_passed(environ_name):
    """
    Is environ for tests? (should be copied)

    :param environ_name: environ name
    :type environ_name: str
    :return: bool -- should be copied or not
    """
    return environ_name.startswith('PYDEVD_') or environ_name == 'VERBOSE'


def build_environ_for_test_environments(for_building_env=False):
    """
    Build dict with environ variables that can be used in tests

    :param for_building_env: (Optional) for building containers
    :type for_building_env: bool
    :return: dict[str, str] -- environment variables
    """
    new_environ = {
        key: value for (key, value) in os.environ.items()
        if is_environ_should_be_passed(key)
    }

    if for_building_env:
        new_environ['MODEL_FILE'] = '/model.bin'

    return new_environ


def get_mocked_model_path(model_name):
    """
    Get path to model's directory

    :param model_name: name of model file without .py
    :type model_name: str
    :return: str -- path to model's directory
    """
    path = os.path.join(TEST_MODELS_LOCATION, model_name)
    if not os.path.exists(path):
        raise Exception('Unknown model {!r}. Path not exists: {!r}'.format(model_name, path))
    return path


class ModelDockerBuilderContainerContext:
    def __init__(self):
        # Base python Docker image
        self._docker_tag = config.SANDBOX_PYTHON_TOOLCHAIN_IMAGE
        self._docker_base_image = None
        self._docker_container = None
        self._docker_client = build_docker_client()
        self._docker_volume = None

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

        self._docker_volume = self._docker_client.volumes.create(driver='local')
        workspace_mount = docker.types.Mount(self.workspace, self._docker_volume.id)

        self._docker_container = self._docker_client.containers.run(
            self._docker_base_image.id,
            command='sleep 99999',  # keep container running for 99999 seconds
            detach=True,  # in the background
            remove=True,  # remove automatically after kill
            environment=build_environ_for_test_environments(True),  # pass environment variables from host machine
            network_mode='host',  # host network is required because we need to connect to pydevd server
            mounts=[
                docker_socket_mount,
                workspace_mount
            ]
        )

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
        self.copy_directory(get_mocked_model_path(model_name), self.workspace)

    def execute_model(self, python_file='run.py'):
        """
        Run model training process

        :param python_file: file to execute
        :type python_file: str
        :return: tuple[str, str, str, str] -- model id, model version, model path, output of execution
        """
        command = 'python3 "{}"'.format(python_file)
        output = self.exec(command, workdir=self.workspace)

        model_name = None
        model_version = None
        model_file = None

        for line in output.splitlines():
            if line.startswith(headers.STDERR_PREFIX):
                line = line[len(headers.STDERR_PREFIX):]
                header, value = line.split(':', maxsplit=1)
                if header == headers.MODEL_NAME:
                    model_name = value
                elif header == headers.MODEL_VERSION:
                    model_version = value
                elif header == headers.MODEL_PATH:
                    model_file = value

        return model_name, model_version, model_file, output

    def build_model_container(self, binary_model_file=None):
        """
        Build model container from model binary with legionctl build

        :param binary_model_file: (Optional) path to binary model file
        :type binary_model_file: str
        :return: tuple[str, str] -- Docker image sha, output of execution
        """
        command = 'legionctl build'

        if binary_model_file:
            command += ' --model-file "{}"'.format(binary_model_file)

        output = self.exec(command, workdir=self.workspace)

        tag = None

        for line in output.splitlines():
            if line.startswith(headers.STDERR_PREFIX):
                line = line[len(headers.STDERR_PREFIX):]
                header, value = line.split(':', maxsplit=1)
                if header == headers.IMAGE_ID_LOCAL:
                    _, tag = value.split(':')

        return tag, output

    def __exit__(self, exc_type, exc_val, exc_tb):
        print_docker_container_logs(self._docker_container)
        self._shutdown_docker_container()


class ModelServeTestBuild:
    """
    Context manager for building and testing models with pyserve
    """

    def __init__(self, model_name, model_version, model_builder):
        """
        Create context

        :param model_name: id of model (uses for building model and model client)
        :type model_name: str
        :param model_version: version of model (passes to model builder)
        :param model_builder: str
        """
        self._model_name = model_name
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
            print('Building model file {} v {}'.format(self._model_name, self._model_version))
            model.reset_context()
            self._model_builder(self._model_name, self._model_version, self._model_path)
            print('Model file has been built')

            print('Creating pyserve')
            additional_environment = {
                'MODEL_FILE': self._model_path
            }
            with patch_config(additional_environment):
                self.application = pyserve.init_application(None)
                self.application.testing = True
                self.client = self.application.test_client()
                self.model_client = ModelClient(url=config.MODEL_HOST, http_client=self.client)

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


def build_requests_reponse_from_flask_client_response(test_response, url):
    """
    Build requests.Response object from Flask test client response

    :param test_response: Flask test client response
    :type test_response: :py:class:`flask.wrappers.Response`
    :param url: requested URL
    :type url: str
    :return: :py:class:`requests.Response` -- response object
    """
    response = requests.Response()
    response.status_code = test_response.status_code
    response.url = url
    response._content = test_response.data
    for header, value in test_response.headers.items():
        response.headers[header] = value
    response._encoding = test_response.charset
    response._content_consumed = True
    return response


def build_requests_mock_function(test_client):
    """
    Build function that should replace requests.request function to Flask test client invocation in tests

    :param test_client: test flask client
    :type test_client: :py:class:`flask.test.FlaskClient`
    :return: Callable[[str, str, dict[str, str], dict[str, str]], requests.Response]
    """

    def func(action, url, data=None, http_headers=None, cookies=None):
        request_data = {'query_string' if action == 'GET' else 'data': data}
        server_name = "localhost"

        for k, v in cookies.items():
            test_client.set_cookie(server_name, k, v)

        test_response = test_client.open(url, method=action, headers=http_headers, **request_data)

        return build_requests_reponse_from_flask_client_response(test_response, url)

    return func


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
        self._docker_client = build_docker_client()

        self._image = self._docker_client.images.get(self._image_id)

        self._model_name = self._image.labels[headers.DOMAIN_MODEL_NAME]
        self._model_version = self._image.labels[headers.DOMAIN_MODEL_VERSION]

        self.container = None
        self.container_id = None
        self.model_port = None
        self.model_information = None
        self.client = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """
        try:
            LOGGER.info('Deploying model {} v {} from image {}'.format(self._model_name,
                                                                       self._model_version,
                                                                       self._image_id))

            additional_environment = {
                **build_environ_for_test_environments()
            }

            container_labels = generate_docker_labels_for_container(self._image)

            api_port_name = '{}/tcp'.format(config.LEGION_PORT)
            ports = {api_port_name: 0}

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
            api_port_information = self.container.attrs['NetworkSettings']['Ports'].get(api_port_name)
            if not api_port_information:
                raise Exception('Port for API has not been registered')

            if len(api_port_information) != 1:
                raise Exception('API port should have exact one binding')

            self.model_port = int(api_port_information[0]['HostPort'])
            LOGGER.info('Model port: {}'.format(self.model_port))

            LOGGER.info('Building client')
            url = 'http://{}:{}'.format('localhost', self.model_port)
            LOGGER.info('Target URI is {}'.format(url))
            self.client = ModelClient(url)

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


_CATCH_LIST_FOR_HTTP_API_JSON_MOCKS = []


def add_response_from_file(url, file_name, method=responses.GET):
    global _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS
    _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS.append(file_name)

    LOGGER.debug('Adding response for {} {} from file {}'.format(method, url, file_name))

    path = os.path.join(TEST_RESPONSES_LOCATION, '{}.json'.format(file_name))
    if not os.path.exists(path):
        LOGGER.debug('Could not find file {} (responses dataset)'.format(path))
        return

    with open(path, 'r') as data_stream:
        data = data_stream.read()

    if data:
        data = json.loads(data)
    else:
        data = None

    responses.add(
        method, url,
        json=data
    )


@contextlib.contextmanager
def catch_http_api_json_calls(*paths, target=None):
    if not target:
        target = 'requests.adapters.HTTPAdapter.send'

    if not paths:
        # If paths are not provided: load from _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS buffer
        # Each call of add_response_from_file() will add path to this buffer
        paths = _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS

    paths_iter = iter(paths)

    old_adapter_send = requests.adapters.HTTPAdapter.send

    def unbound_on_send(adapter, request, *a, **kwargs):
        result = old_adapter_send(adapter, request, *a, **kwargs)
        LOGGER.debug('Trying to persist result of {} {}'.format(request.method, request.url))
        try:
            path = next(paths_iter)
        except StopIteration:
            raise Exception('Could not find path to save results of {} {}'.format(request.method, request.url))

        full_path = os.path.join(TEST_RESPONSES_LOCATION, '{}.json'.format(path))

        LOGGER.debug('Response for {} {} has been persisted to {}'.format(request.method, request.url, full_path))

        with open(full_path, 'w') as output_stream:
            json.dump(result.json(), output_stream, indent=2)

        return result

    patcher = patch(target, new=unbound_on_send)
    patcher.start()
    yield
    patcher.stop()


def activate_http_api_json_calls_catcher(*paths, target=None):
    global _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS
    _CATCH_LIST_FOR_HTTP_API_JSON_MOCKS.clear()

    def wrapper(func):
        def wrapped(*args, **kwargs):
            with catch_http_api_json_calls(*paths, target=target):
                return func(*args, **kwargs)

        return wrapped

    return wrapper
