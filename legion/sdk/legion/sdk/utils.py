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
"""
legion utils functional
"""
import contextlib
import datetime
import distutils.dir_util  # pylint: disable=E0611,E0401
import getpass
import inspect
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import zipfile

from jinja2 import Environment, PackageLoader, select_autoescape

from legion.sdk import config
from legion.sdk.containers import headers

KUBERNETES_STRING_LENGTH_LIMIT = 63
LOGGER = logging.getLogger(__name__)
MODEL_NAMING_UID_ENV = 'JUPYTERHUB_USER', 'NB_USER', 'BUILD_ID'


def render_template(template_name, values=None):
    """
    Render template with parameters

    :param template_name: name of template without path (all templates should be placed in legion.templates directory)
    :param values: dict template variables or None
    :return: str rendered template
    """
    env = Environment(
        loader=PackageLoader(__name__, 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    if not values:
        values = {}

    template = env.get_template(template_name)
    return template.render(values)


class EdiHTTPException(Exception):
    """
    Exception for EDI server (with HTTP code)
    """

    def __init__(self, http_code, message):
        """
        Build exception

        :param http_code: HTTP code
        :type http_code: int
        :param message: message for user
        :type message: str
        """
        super(EdiHTTPException, self).__init__(message)
        self.http_code = http_code
        self.message = message


class EdiHTTPAccessDeniedException(EdiHTTPException):
    """
    Exception for EDI server -- access denied
    """

    def __init__(self, message='Access denied'):
        """
        Build exception

        :param message: message for user
        :type message: str
        """
        super(EdiHTTPAccessDeniedException, self).__init__(403, message)


def detect_ip():
    """
    Get current machine IP address

    :return: str -- IP address
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    addr = sock.getsockname()[0]
    sock.close()
    return addr


def escape(unescaped_string):
    """
    Escape string (replace .:& with -)

    :param unescaped_string: source string
    :type unescaped_string: str
    :return: str -- escaped string
    """
    return unescaped_string.replace('.', '-').replace(':', '-').replace('&', '-')


def remove_directory(path):
    """
    Remove directory and all subdirectories or file

    :param path: path to directory or file
    :type path: str
    :return: None
    """
    try:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

            os.rmdir(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            raise Exception('Not a directory or file: %s' % path)
    finally:
        pass


class TemporaryFolder:
    """
    Temporary folder representation with context manager (temp. directory deletes of context exit)
    """

    def __init__(self, *args, change_cwd=False, **kwargs):
        """
        Build temp. folder representation using tempfile.mkdtemp

        :param args: tempfile.mkdtemp args
        :type args: tuple
        :param change_cwd: (Optional) change CWD to temporary path
        :type change_cwd: bool
        :param kwargs: tempfile.mkdtemp kwargs
        :type kwargs: dict
        """
        self._old_cwd = os.getcwd()
        self._change_cwd = change_cwd
        new_kwargs = kwargs.copy()

        temp_directory_override = config.TEMP_DIRECTORY
        if temp_directory_override:
            new_kwargs.update({'dir': temp_directory_override})

        LOGGER.debug('Creating temporary directory with args={!r} and kwargs={!r}'.format(args,
                                                                                          new_kwargs))

        self._path = tempfile.mkdtemp(*args, **new_kwargs)

    @property
    def path(self):
        """
        Get path to temp. folder

        :return: str -- path
        """
        return self._path

    @property
    def change_cwd(self):
        """
        Has directory been changed or not

        :return: bool
        """
        return self._change_cwd

    @property
    def old_cwd(self):
        """
        Old CWD

        :return: str
        """
        return self._old_cwd

    def remove(self):
        """
        Try to remove temporary folder (without exceptions)

        :return: None
        """
        remove_directory(self._path)

    def __enter__(self):
        """
        Return self on context enter

        :return: :py:class:`legion.utils.TemporaryFolder`
        """
        if self.change_cwd:
            os.chdir(self.path)
        return self

    def __exit__(self, exit_type, value, traceback):
        """
        Call remove on context exit

        :param exit_type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        if self.change_cwd:
            os.chdir(self.old_cwd)
        self.remove()


class Colors:
    """
    Terminal colors
    """

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def normalize_name(name, dns_1035=False, kubernetes_compatible=False):
    """
    Normalize name

    :param name: name to normalize
    :type name: str
    :param dns_1035: (Optional) use DNS-1035 format, by default False
    :type dns_1035: bool
    :param kubernetes_compatible: (Optional) fit into kubernetes length limitations
    :type kubernetes_compatible: bool
    :return: str -- normalized name
    """
    invalid_delimiters = ' ', '_', '+'
    invalid_chars = r'[^a-zA-Z0-9\-\.]'
    if dns_1035:
        invalid_chars = r'[^a-zA-Z0-9\-]'
        invalid_delimiters = ' ', '_', '+', '.'

    for char in invalid_delimiters:
        name = name.replace(char, '-')

    value = re.sub(invalid_chars, '', name)
    if kubernetes_compatible:
        value = value[:KUBERNETES_STRING_LENGTH_LIMIT]

    return value


def copy_file(source_file, target_file):
    """
    Copy file from one location to another

    :param source_file: source file location
    :type source_file: str
    :param target_file: target file location
    :type target_file: str
    :return: None
    """
    shutil.copyfile(source_file, target_file)


def copy_directory_contents(source_directory, target_directory):
    """
    Copy all files from source directory to targer directory

    :param source_directory: source directory
    :type source_directory: str
    :param target_directory: target directory
    :type target_directory: str
    :return: None
    """
    distutils.dir_util.copy_tree(source_directory, target_directory)


def save_file(temp_file, target_file, remove_after_delete=False):
    """
    Upload local file to external resource

    :param temp_file: path to file on local machine
    :type temp_file: str
    :param target_file: path to file on external resource
    :type target_file: str
    :param remove_after_delete: remove local file
    :type remove_after_delete: bool
    :return: str -- path to file on external resource
    """
    try:
        if os.path.abspath(temp_file) != os.path.abspath(target_file):
            shutil.copy2(temp_file, target_file)
        result_path = os.path.abspath(target_file)
    finally:
        if remove_after_delete:
            os.remove(temp_file)

    return result_path


@contextlib.contextmanager
def extract_archive_item(path, subpath):
    """
    Extract item from archive using context manager to temporary directory

    :param path: path to archive
    :type path: str
    :param subpath: path to file in archive
    :type subpath: str
    :return: str -- path to temporary extracted file
    """
    with TemporaryFolder() as temp_directory:
        try:
            with zipfile.ZipFile(path, 'r') as stream:
                target_path = os.path.join(temp_directory.path, subpath)
                extracted_path = stream.extract(subpath, target_path)

                yield extracted_path
        except zipfile.BadZipFile:
            raise Exception('File {} is not a archive'.format(path))


def get_git_revision(file, use_short_hash=True):
    """
    Get current GIT revision of file or directory

    :param file: path to file or directory for check
    :type file: str
    :param use_short_hash: return shorten revision id
    :type use_short_hash: bool
    :return: str or None -- revision id
    """
    try:
        directory = file
        if not os.path.isdir(directory):
            directory = os.path.dirname(file)

        revision = subprocess.check_output(['git', 'rev-parse',
                                            '--short' if use_short_hash else '',
                                            'HEAD'],
                                           cwd=directory)
    except subprocess.CalledProcessError:
        return None

    if isinstance(revision, bytes):
        revision = revision.decode('utf-8')

    return revision.strip()


def send_header_to_stderr(header, value):
    """
    Send header with specific prefix to stderr

    :param header: name of header (without common prefix)
    :type header: str
    :param value: value of header
    :type value: str
    :return: None
    """
    message = '{}{}:{}'.format(headers.STDERR_PREFIX, header, value)
    print(message, file=sys.__stderr__, flush=True)


def model_properties_storage_name(model_id, model_version):
    """
    Construct properties storage name

    :param model_id: model ID
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: str -- name of properties storage
    """
    return normalize_name('model-{}-{}'.format(model_id, model_version), dns_1035=True)


def parse_value_to_type(value, target_type):
    """
    Parse string value to target type

    :param value: value to parse
    :type value: any
    :param target_type: target python type
    :type target_type: :py:class:`type`
    :return: :py:class:`type`() -- target instance
    """
    if target_type == bool:
        return config.cast_bool(str(value))
    else:
        return target_type(value)


def get_list_of_requirements():
    """
    Get list of requirements stored in data/Pipfile.lock

    :return: list[(str, str)] -- list of requirements in the "package==version" format
    """
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'Pipfile.lock')
    if not os.path.exists(file_path):
        # TODO: fix
        return []
        raise Exception('File with requirements ({}) is not exists'.format(file_path))

    with open(file_path, 'r') as file_stream:
        file_data = json.load(file_stream)

    file_objects = file_data.get('default', {})
    return sorted([
        (key, value['version'][2:])
        for (key, value) in file_objects.items()
    ], key=lambda item: item[0])


def get_installed_packages():
    """
    Get list of installed packages

    :return: list[(str, str)] -- list of installed packages in the "package==version" format
    """
    import pkg_resources
    return sorted([
        (item.key, item.version)
        for item in pkg_resources.working_set  # pylint: disable=E1133
    ], key=lambda item: item[0])


def deduce_extra_version():
    """
    Deduce extra version based on date, user, commit

    :return: str -- extra version string
    """
    date_string = datetime.datetime.now().strftime('%y%m%d%H%M%S')

    valid_user_names = [os.getenv(env) for env in MODEL_NAMING_UID_ENV if os.getenv(env)]
    user_id = valid_user_names[0] if valid_user_names else getpass.getuser()

    commit_id = get_git_revision(os.getcwd())
    if not commit_id:
        commit_id = '0000'

    return '.'.join([date_string, user_id, commit_id])


def deduce_model_file_name(model_id, model_version):
    """
    Get model file name

    :param model_id: ID of model
    :type model_id: str
    :param model_version: version of model
    :type model_version: str
    :return: str -- auto deduced file name
    """
    file_name = '%s-%s+%s.model' % (model_id, str(model_version), deduce_extra_version())

    default_prefix = config.LOCAL_DEFAULT_RESOURCE_PREFIX
    if default_prefix:
        return os.path.join(default_prefix, file_name)

    return file_name


def get_function_description(callable_object):
    """
    Gather information about callable object to string

    :param callable_object: callable object to analyze
    :type callable_object: Callable[[], any]
    :return: str -- object description
    """
    object_class_name = callable_object.__class__.__name__
    if not callable(callable_object):
        return '<not callable object: {}>'.format(object_class_name)

    object_name = callable_object.__name__
    module_name = inspect.getmodule(callable_object)
    return '<{} {} in {}>'.format(object_class_name, object_name, module_name)


def ensure_function_succeed(function_to_call, retries, timeout, boolean_check=False):
    """
    Try to call function till it will return not None object.
    Raise if there are no retries left

    :param function_to_call: function to be called
    :type function_to_call: Callable[[], any]
    :param retries: count of retries
    :type retries: int
    :param timeout: timeout between retries
    :type timeout: int
    :param boolean_check: (Optional) check function for True-able value (by default value is checked for not None value)
    :type boolean_check: bool
    :return: Any -- result of successful function call or None if no retries left
    """
    function_description = get_function_description(function_to_call)
    for no in range(retries):
        LOGGER.debug('Calling {}'.format(function_description))
        result = function_to_call()

        if boolean_check:
            if result:
                return result
        else:
            if result is not None:
                return result

        if no < retries:
            LOGGER.debug('Retry {}/{} was failed'.format(no + 1, retries))
        if no < retries - 1:
            LOGGER.debug('Waiting {}s before next retry analysis'.format(timeout))
            time.sleep(timeout)

    LOGGER.error('No retries left for function {}'.format(function_description))
    return False if boolean_check else None
