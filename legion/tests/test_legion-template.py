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
Legion Templating System unit tests
"""
import logging
import unittest2
import os
import shutil
from threading import Thread

import asyncio

from legion.template import LegionTemplateEngine
import legion.utils

TEST_FILES_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'templates')


def _setup_template_value(value_file_name, source_file_name):
    source = os.path.join(TEST_FILES_LOCATION, source_file_name)
    target = os.path.join(TEST_FILES_LOCATION, value_file_name)

    shutil.copyfile(source, target)


class TestLegionTemplateEngine(unittest2.TestCase):
    """
    Unit tests for template system
    """
    SLEEP_INTERVAL_IN_SEC = 3

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def assertStringEqualToTemplateFileWithIterations(self, actual_string_getter, expected_file, msg=None):
        expected_file_path = os.path.join(TEST_FILES_LOCATION, expected_file)
        with open(expected_file_path, 'r') as expected_file_stream:
            expected_data = expected_file_stream.read().strip('\n\r ')
            actual_string_stripped = None

        def check_function():
            nonlocal actual_string_getter, actual_string_stripped, expected_file, expected_data
            actual_string = actual_string_getter()
            actual_string_stripped = actual_string.strip('\n\r ')

            print('Expected (from {}):\n{}\nActual:\n{}\n'.format(expected_file, expected_data, actual_string_stripped))
            return actual_string_stripped == expected_data

        legion.utils.ensure_function_succeed(check_function, 5, 2, boolean_check=True)
        self.assertEqual(actual_string_stripped, expected_data, msg)

    @unittest2.skip
    def test_empty_template(self):
        """
        Test exception generation for empty template file
        """
        with TemplateRenderThread('yaml_file_empty.t', 'yaml_file_empty.tmp.out') as renderer:
            def check_render_got_exception():
                return renderer.raised_exception

            self.assertTrue(legion.utils.ensure_function_succeed(check_render_got_exception, 5, 3))

            self.assertIsNotNone(renderer.raised_exception)
            self.assertIsInstance(renderer.raised_exception, Exception)
            self.assertEqual(renderer.raised_exception.args[0], 'Template doesnt use any plugin')

    def test_yaml_file_watch(self):
        """
        Test a yaml file watch module
        """
        # Set initial data
        _setup_template_value('yaml_file_test_values.tmp.yml', 'yaml_file_test_values_1.yml')

        with TemplateRenderThread('yaml_file_test.t', 'yaml_file_test.tmp.out') as renderer:
            self.assertStringEqualToTemplateFileWithIterations(renderer.output_data_getter,
                                                               'yaml_file_test_values_expected_1.out')

            # Set updated data
            print('Updating file..')
            _setup_template_value('yaml_file_test_values.tmp.yml', 'yaml_file_test_values_2.yml')
            self.assertStringEqualToTemplateFileWithIterations(renderer.output_data_getter,
                                                               'yaml_file_test_values_expected_2.out')

    def test_duo_yaml_files_watch(self):
        """
        Test duo yaml files watch module
        """
        # Set initial data
        _setup_template_value('yaml_file_test_values_first.tmp.yml', 'yaml_file_test_values_1.yml')
        _setup_template_value('yaml_file_test_values_second.tmp.yml', 'yaml_file_test_values_2.yml')

        with TemplateRenderThread('yaml_file_test_duo.t', 'yaml_file_test_duo.tmp.out') as renderer:
            self.assertStringEqualToTemplateFileWithIterations(renderer.output_data_getter,
                                                               'yaml_file_test_duo_expected_1.out')

            # Set updated data
            print('Updating first file..')
            _setup_template_value('yaml_file_test_values_first.tmp.yml', 'yaml_file_test_values_2.yml')
            self.assertStringEqualToTemplateFileWithIterations(renderer.output_data_getter,
                                                               'yaml_file_test_duo_expected_2.out')

            # Set updated data
            print('Updating second file..')
            _setup_template_value('yaml_file_test_values_second.tmp.yml', 'yaml_file_test_values_1.yml')
            self.assertStringEqualToTemplateFileWithIterations(renderer.output_data_getter,
                                                               'yaml_file_test_duo_expected_3.out')


class TemplateRenderThread(Thread):
    """
    A thread with a render loop for file watch test.
    """
    def __init__(self, template_path, output_path):
        """
        Init a Thread object.

        :param template_path: a path to a template file
        :type template_path: str
        :param output_path: a path to an output file
        :type output_path: str
        """
        Thread.__init__(self)
        self.name = 'template_render_loop'
        self.daemon = True
        self.template_path = os.path.join(TEST_FILES_LOCATION, template_path)
        self.output_path = os.path.join(TEST_FILES_LOCATION, output_path)
        self.event_loop = None
        self.raised_exception = None

    def run(self):
        """
        Run a render loop for file watch test.

        :return: None
        """
        try:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            template_system = LegionTemplateEngine(self.template_path, self.output_path)
            template_system.render_loop()

        except Exception as exception:
            self.raised_exception = exception
            raise self.raised_exception

    def __enter__(self):
        """
        A function of Context manager, which starts a thread with a render loop.

        :return: None
        """
        if os.path.exists(self.output_path):
            os.unlink(self.output_path)

        self.start()

        if not legion.utils.ensure_function_succeed(lambda: os.path.exists(self.output_path),
                                                    5, 2, boolean_check=True):
            raise Exception('File {} is not existed'.format(self.output_path))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        A function of Context manager, which stops an event loop of a thread.

        :return: None
        """
        if self.event_loop:
            self.event_loop.stop()

    @property
    def output_data(self):
        """
        Get data stored if target file

        :return: str
        """
        with open(self.output_path, 'r') as file:
            return file.read()

    @property
    def output_data_getter(self):
        """
        Build output data getter

        :return: Callable[[], str]
        """
        return lambda: self.output_data


if __name__ == '__main__':
    unittest2.main()
