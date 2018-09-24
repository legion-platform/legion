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
import datetime
import contextlib
import os
import getpass
import distutils.dir_util
import re
import logging
import shutil
import socket
import subprocess
import sys
import time
import tempfile
import zipfile
import inspect

import legion.config
import legion.containers.headers

import docker
import requests
import requests.auth
from jinja2 import Environment, PackageLoader, select_autoescape


KUBERNETES_STRING_LENGTH_LIMIT = 63
LOGGER = logging.getLogger(__name__)


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

    def __init__(self, *args, **kwargs):
        """
        Build temp. folder representation using tempfile.mkdtemp

        :param args: tempfile.mkdtemp args
        :type args: tuple
        :param kwargs: tempfile.mkdtemp kwargs
        :type kwargs: dict
        """
        self._path = tempfile.mkdtemp(*args, **kwargs)

    @property
    def path(self):
        """
        Get path to temp. folder

        :return: str -- path
        """
        return self._path

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
        return self

    def __exit__(self, exit_type, value, traceback):
        """
        Call remove on context exit

        :param exit_type: -
        :param value: -
        :param traceback: -
        :return: None
        """
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
    invalid_chars = '[^a-zA-Z0-9\-\.]'
    if dns_1035:
        invalid_chars = '[^a-zA-Z0-9\-]'
        invalid_delimiters = ' ', '_', '+', '.'

    for char in invalid_delimiters:
        name = name.replace(char, '-')

    value = re.sub(invalid_chars, '', name)
    if kubernetes_compatible:
        value = value[:KUBERNETES_STRING_LENGTH_LIMIT]

    return value


def is_local_resource(path):
    """
    Check if path is local resource

    :param path:
    :type path: str
    :return: bool -- is path for local resource
    """
    if any(path.lower().startswith(prefix) for prefix in ['http://', 'https://', '//']):
        return False

    if '://' in path:
        raise Exception('Unknown or unavailable resource: %s' % path)

    return True


def normalize_external_resource_path(path):
    """
    Normalize external resource path

    :param path: non-normalized resource path
    :type path: str
    :return: str -- normalized path
    """
    default_protocol = os.getenv(*legion.config.EXTERNAL_RESOURCE_PROTOCOL)
    default_host = os.getenv(*legion.config.EXTERNAL_RESOURCE_HOST)

    if path.lower().startswith('//'):
        path = '%s:%s' % (default_protocol, path)

    first_double_slash = path.find('//')

    if first_double_slash < 0:
        raise Exception('Cannot found double slash')

    if len(path) == first_double_slash + 2:
        return path + default_host
    elif len(path) > first_double_slash + 2 and path[first_double_slash + 2] == '/':
        return path[:first_double_slash] + '//' + default_host + path[first_double_slash + 2:]

    return path


def _get_auth_credentials_for_external_resource():
    """
    Get HTTP auth credentials for requests module

    :return: :py:class:`requests.auth.HTTPBasicAuth` -- credentials
    """
    user = os.getenv(*legion.config.EXTERNAL_RESOURCE_USER)
    password = os.getenv(*legion.config.EXTERNAL_RESOURCE_PASSWORD)

    if user and password:
        return requests.auth.HTTPBasicAuth(user, password)

    return None


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
        if is_local_resource(target_file):
            if os.path.abspath(temp_file) != os.path.abspath(target_file):
                shutil.copy2(temp_file, target_file)
            result_path = os.path.abspath(target_file)
        else:
            url = normalize_external_resource_path(target_file)

            with open(temp_file, 'rb') as file:
                auth = _get_auth_credentials_for_external_resource()
                response = requests.put(url,
                                        data=file,
                                        auth=auth)
                if response.status_code >= 400:
                    raise Exception('Wrong status code %d returned for url %s' % (response.status_code, url))

            result_path = url

    finally:
        if remove_after_delete:
            os.remove(temp_file)

    return result_path


def download_file(target_file):
    """
    Download file from external resource and return path to file on local machine

    :param target_file: path to file on external resource
    :type target_file: str
    :return: str -- path to file on local machine
    """
    if is_local_resource(target_file):
        return target_file

    # If external resource (only HTTP at this time)
    url = normalize_external_resource_path(target_file)
    name = target_file.split('/')[-1]
    credentials = _get_auth_credentials_for_external_resource()
    response = requests.get(url,
                            stream=True,
                            verify=False,
                            auth=credentials)
    if response.status_code >= 400 or response.status_code < 200:
        raise Exception('Cannot load resource: %s. Returned status code: %d' % (url, response.status_code))

    temp_file = tempfile.mktemp(suffix=name)

    with open(temp_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

    return os.path.abspath(temp_file)


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


class ExternalFileReader:
    """
    External file reader for opening files from http://, https:// and local FS
    """

    def __init__(self, path):
        """
        Create external file reader

        :param path: path to file
        :type path: str
        """
        self._path = path
        self._local_path = None
        self._is_external_path = not is_local_resource(self._path)

    @property
    def path(self):
        """
        Get path to file on local machine

        :return:
        """
        return self._local_path

    def _download(self):
        """
        Download external resource

        :return: None
        """
        if not self._local_path:
            if self._is_external_path:
                self._local_path = download_file(self._path)
            else:
                self._local_path = self._path

    def __enter__(self):
        """
        Return self on context enter

        :return: :py:class:`legion.utils.ExternalFileReader`
        """
        self._download()
        return self

    def __exit__(self, exit_type, value, traceback):
        """
        Call remove on context exit

        :param exit_type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        if self._is_external_path:
            remove_directory(self._local_path)


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
    message = '{}{}:{}'.format(legion.containers.headers.STDERR_PREFIX, header, value)
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


def string_to_bool(value):
    """
    Convert string to bool

    :param value: string or bool
    :type value: str or bool
    :return: bool
    """
    if isinstance(value, bool):
        return value

    return value.lower() in ['true', '1', 't', 'y', 'yes']


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
        return string_to_bool(str(value))
    else:
        return target_type(value)


def deduce_model_file_name(model_id, model_version):
    """
    Get model file name

    :param model_id: ID of model
    :type model_id: str
    :param model_version: version of model
    :type model_version: str
    :return: str -- auto deduced file name
    """
    date_string = datetime.datetime.now().strftime('%y%m%d%H%M%S')

    valid_user_names = [os.getenv(env) for env in legion.config.MODEL_NAMING_UID_ENV if os.getenv(env)]
    user_id = valid_user_names[0] if valid_user_names else getpass.getuser()

    commit_id = get_git_revision(os.getcwd())
    if not commit_id:
        commit_id = '0000'

    file_name = '%s-%s+%s.%s.%s.model' % (model_id, str(model_version), date_string, user_id, commit_id)

    if string_to_bool(os.getenv(*legion.config.EXTERNAL_RESOURCE_USE_BY_DEFAULT)):
        return '///%s' % file_name

    default_prefix = os.getenv(*legion.config.LOCAL_DEFAULT_RESOURCE_PREFIX)
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
