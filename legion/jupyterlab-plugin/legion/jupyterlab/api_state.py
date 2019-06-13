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
Declare plugin state handlers
"""
import os
import typing
import tempfile
import subprocess


class ApiState:
    """
    Plugin state handlers (stores plugin state)
    """

    def __init__(self):
        """
        Initialize state
        """
        self._local_build_process = None
        # Create temporary directory (without removal)
        self._local_build_storage = os.path.join(tempfile.mkdtemp(), 'log')
        with open(self._local_build_storage, 'w') as log_stream:
            log_stream.write('')

    def register_local_build(self, process: subprocess.Popen):
        """
        Register local build

        :param process: local build process
        :type process: subprocess.Popen
        :return: None
        """
        self._local_build_process = process

    @property
    def local_build_process(self) -> typing.Optional[subprocess.Popen]:
        """
        Get registered local build process or None

        :return: subprocess.Popen or None -- previously registered local build process
        """
        return self._local_build_process

    @property
    def local_build_storage(self) -> str:
        """
        Get storage for local build logs
        """
        return self._local_build_storage
