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
DRun utils functional
"""

import socket
import subprocess
import re
import tempfile
import os
import sys
import shutil
import requests
import requests.auth

import drun.env

import docker


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

        :return: :py:class:`drun.utils.TemporaryFolder`
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Call remove on context exit

        :param type: -
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


def normalize_name(name):
    """
    Normalize name

    :param name: name to normalize
    :type name: str
    :return: str -- normalized name
    """
    name = name.replace(' ', '_')
    return re.sub('[^a-zA-Z0-9\-_\.]', '', name)


def normalize_name_to_dns_1123(name):
    """
    Normalize name to DNS-1123

    :param name: name to normalize
    :type name: str
    :return: str -- normalized name
    """
    name = name.replace(' ', '-')
    name = name.replace('_', '-')
    return re.sub('[^a-zA-Z0-9\-\.]', '', name)


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
    default_protocol = os.getenv(*drun.env.EXTERNAL_RESOURCE_PROTOCOL)
    default_host = os.getenv(*drun.env.EXTERNAL_RESOURCE_HOST)

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
    user = os.getenv(*drun.env.EXTERNAL_RESOURCE_USER)
    password = os.getenv(*drun.env.EXTERNAL_RESOURCE_PASSWORD)

    if user and password and len(user) > 0:
        return requests.auth.HTTPBasicAuth(user, password)

    return None


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
            result_path = target_file
        else:
            url = normalize_external_resource_path(target_file)

            with open(temp_file, 'rb') as file:
                auth = _get_auth_credentials_for_external_resource()
                response = requests.put(url,
                                        data=file,
                                        auth=auth)
                if 400 <= response.status_code:
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
    temp_file = tempfile.mktemp(suffix=name)

    with open(temp_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

    return os.path.abspath(temp_file)


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

        :return: :py:class:`drun.utils.ExternalFileReader`
        """
        self._download()
        return self

    def __exit__(self, type, value, traceback):
        """
        Call remove on context exit

        :param type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        if self._is_external_path:
            remove_directory(self._local_path)


class DockerContainerContext:
    """
    Context for working with docker containers
    """

    def __init__(self, image, pull_from_server=True, **kwargs):
        """
        Create context for docker container

        :param image: Docker image name
        :type image: str
        :param pull_from_server: pull image from docker registry
        :type  pull_from_server: bool
        :param kwargs: arguments for creation of container
        :type kwargs: *dict
        """
        self._client = docker.from_env()
        self._container = None
        self._image = image
        self._pull_from_server = pull_from_server
        self._kwargs = kwargs

    def __enter__(self):
        """
        Return self on context enter

        :return: :py:class:`drun.utils.DockerContainerContext`
        """
        if self._pull_from_server:
            self._client.images.pull(self._image)

        self._container = self._client.containers.run(self._image, detach=True, remove=True, **self._kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Call stop and remove on context exit

        :param type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        try:
            self._container.stop()
        except Exception:
            pass

    @property
    def container(self):
        """
        Get docker container

        :return: :py:class:`docker.containers.Container`
        """
        return self._client.containers.get(self._container.id)


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
    message = 'X-DRun-%s:%s' % (header, value)
    print(message, file=sys.__stderr__, flush=True)
