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
import re
import tempfile
import os
import sys


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
        try:
            for root, dirs, files in os.walk(self.path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        finally:
            pass

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
