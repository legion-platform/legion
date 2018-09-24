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
Robot test library - process wrapper for gathering streams without PIPEs
"""
import tempfile
import os

import robot.libraries.Process

import legion_test.robot.framework_extensions


def build_configuration_and_files(configuration):
    """
    Parse Run Process arguments and create files for streams without arguments

    :param configuration: robot call argument
    :type configuration: dict[str, str]
    :return: tuple(dict[str, str], list[str]) -- tuple of new configuration and list of temporary files
    """
    new_files = []
    for stream in ('stdout', 'stderr'):
        if stream not in configuration:
            _1, new_file = tempfile.mkstemp(prefix='robot.run_process.')
            configuration[stream] = new_file
            new_files.append(new_file)
    return configuration, new_files


class Process:
    """
    Native process library wrapper for gathering streams without PIPEs
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    @staticmethod
    def run_process_without_pipe(command, *arguments, **configuration):
        """
        Wrapper around `Run Process` function from standard `Process` library.
        Uses temporary files instead of PIPEs for stdout and stderr streams.
        Removes files at the end of operation.
        Runs a process and waits for it to complete.
        """
        process_lib = legion_test.robot.framework_extensions.get_imported_library_instance('Process')
        if not process_lib:
            raise Exception('Robot native library Process has not been imported')

        result = None
        new_configuration, temporary_files = build_configuration_and_files(configuration)
        try:
            result = process_lib.run_process(command, *arguments, **new_configuration)
            _1, _2 = result.stdout, result.stderr  # force loading data from file streams
        finally:
            for file in temporary_files:
                try:
                    os.remove(file)
                except Exception as file_removal_exception:
                    print('Cannot remove temporary file {!r}: {}'.format(file, file_removal_exception))

        return result
