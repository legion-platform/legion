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
import robot.running


def build_configuration_and_files(configuration, temp_directory=None):
    """
    Parse Run Process arguments and create files for streams without arguments

    :param configuration: robot call argument
    :type configuration: dict[str, str]
    :param temp_directory: (Optional) directory to store temp files, by default - system temp
    :type temp_directory: str
    :return: tuple(dict[str, str], list[str]) -- tuple of new configuration and list of temporary files
    """
    new_files = []
    new_configuration = configuration.copy()
    for stream in ('stdout', 'stderr'):
        if stream not in configuration:
            _1, new_file = tempfile.mkstemp(prefix='robot.run_process.', dir=temp_directory)
            print('Temporary file {!r} has been created for stream {!r}. Directory = {!r}'
                  .format(new_file, stream, temp_directory))
            new_configuration[stream] = new_file
            new_files.append(new_file)
    return new_configuration, new_files


class Process(robot.libraries.Process.Process):
    """
    Native process library wrapper for gathering streams without PIPEs
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def run_process_without_pipe(self, command, *arguments, **configuration):
        """
        Wrapper around `Run Process` function from standard `Process` library.
        Uses temporary files instead of PIPEs for stdout and stderr streams.
        Removes files at the end of operation.
        Runs a process and waits for it to complete.
        """
        variables = robot.running.context.EXECUTION_CONTEXTS.current.variables.current.as_dict(decoration=False)
        new_configuration, temporary_files = build_configuration_and_files(configuration,
                                                                           variables.get('TEMP_DIRECTORY'))
        result = None
        try:
            result = self.run_process(command, *arguments, **new_configuration)
            _1, _2 = result.stdout, result.stderr  # force loading data from file streams
        finally:
            for temp_file in temporary_files:
                try:
                    print('Removing temporary file {!r}'.format(temp_file))
                    os.remove(temp_file)
                except Exception as file_removal_exception:
                    print('Cannot remove temporary file {!r}: {}'.format(temp_file, file_removal_exception))

        return result
