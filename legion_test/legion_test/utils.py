#
#    Copyright 2018 EPAM Systems
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
import logging
import threading
import time
import re

LOGGER = logging.getLogger(__name__)


def wait_until(condition, iteration_duration=5, iterations=10):
    """
    Wait until condition would be true

    :param condition: callable condition that returns bool value
    :type condition: Callable
    :param iteration_duration: duration between checks in seconds
    :type iteration_duration: int
    :param iterations: maximum count of iterations
    :type iterations: int
    :return: object or False -- result or False
    """
    for _ in range(iterations):
        result = condition()
        if result:
            return result

        time.sleep(iteration_duration)

    return False


def normalize_name(name, dns_1035=False):
    """
    Normalize name

    :param name: name to normalize
    :type name: str
    :param dns_1035: (Optional) use DNS-1035 format, by default False
    :type dns_1035: bool
    :return: str -- normalized name
    """
    invalid_delimiters = ' ', '_', '+'
    invalid_chars = '[^a-zA-Z0-9\-\.]'
    if dns_1035:
        invalid_chars = '[^a-zA-Z0-9\-]'
        invalid_delimiters = ' ', '_', '+', '.'

    for char in invalid_delimiters:
        name = name.replace(char, '-')

    return re.sub(invalid_chars, '', name)


class ContextThread(threading.Thread):
    """
    Context manager thread
    """

    def __init__(self, threaded_function, name='ContextThread'):
        """
        Construct context manager

        :param threaded_function: function to be runned parallel
        :type threaded_function: callable
        :param name: name of thread
        :type name: str
        """
        threading.Thread.__init__(self, name=name)
        self.daemon = True
        self._function = threaded_function
        self._ready = False

    @property
    def is_thread_ready(self):
        """
        Check is thread ready

        :return: bool -- is thread ready or not
        """
        return self._ready

    def run(self):
        """
        Run thread

        :return: None
        """
        try:
            self._ready = True
            self._function()
        finally:
            LOGGER.debug('ContextThread finished his work')

    def stop(self):
        """
        Stop thread

        :return: None
        """
        try:
            self.join(0)
        finally:
            LOGGER.debug('ContextThread has been stopped')

    def __enter__(self):
        """
        Enter thread

        :return: None
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop thread on exit

        :param exc_type: exception type
        :param exc_val: exception value
        :param exc_tb: exception traceback
        :return: None
        """
        self._ready = False
        self.stop()