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
Listener that kills all active processes and outputs their stdout/stderr streams.
"""

import os
import signal
import sys

import robot.libraries.Process
import robot.running


ROBOT_LISTENER_API_VERSION = 3
TARGET_STREAM = sys.__stderr__
KILL_SIGNAL = signal.SIGKILL


def get_imported_library_instance(name):
    """
    Get library instance from storage

    :param name: name of library
    :type name: str
    :return: library instance or None (e.g. robot.libraries.Process.Process instance)
    """
    context = robot.running.context.EXECUTION_CONTEXTS.current
    namespace = context.namespace
    imported = namespace._kw_store.libraries
    if name not in imported:
        return None
    return imported[name]._libinst


def report_process_output(process_name, stream_name, stream):
    """
    Report process'es stream

    :param process_name: name of process
    :type process_name: str
    :param stream_name: name of stream, e.g. stdout
    :type stream_name: str
    :param stream: stream
    :type stream: bytes or str
    :return: None
    """
    if not stream:
        print('Process {!r} has no {}'.format(process_name, stream_name), file=TARGET_STREAM)
    else:
        if isinstance(stream, bytes):
            stream = stream.decode('utf-8')
        print('Process {!r} has {} output:\n{}'.format(process_name, stream_name, stream), file=TARGET_STREAM)


def kill_and_report_process(popen_object):
    """
    Kill and report process stderr and stdout

    :param popen_object: instance of process
    :type popen_object: :py:class:`subprocess.Popen`
    :return: None
    """
    try:
        os.kill(popen_object.pid, KILL_SIGNAL)
    except ProcessLookupError:
        print('Cannot find process by id #{}'.format(popen_object.pid), file=TARGET_STREAM)
    except Exception as kill_exception:
        print('Cannot kill process: {!r}'.format(kill_exception), file=TARGET_STREAM)

    try:
        report_process_output(popen_object.args, 'stdout', popen_object.stdout.read())
        report_process_output(popen_object.args, 'stderr', popen_object.stderr.read())
    except Exception as gather_exception:
        print('Cannot gather process #{} logs: {!r}'.format(popen_object.pid, gather_exception), file=TARGET_STREAM)


def end_test(test, result):
    """
    Listener for Robot's "end of test" event

    :param test: test
    :param result: test result
    :return: None
    """
    if not result.passed:
        process_lib = get_imported_library_instance('Process')
        if process_lib:
            all_processes = process_lib._processes._connections
            all_results = process_lib._results

            active_processes = [process for process in all_processes
                                if process in all_results and all_results[process].rc is None]

            if active_processes:
                print('Some hanging processes have been detected for failed test {!r}'.format(
                    result.name
                ), file=TARGET_STREAM)

                for process in active_processes:
                    print('Killing active process {!r} for test {!r} because of {!r}'.format(
                        process.args,
                        result.name,
                        result.message
                    ), file=TARGET_STREAM)
                    kill_and_report_process(process)
