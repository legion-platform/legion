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
Legion Templating System
"""
import logging
import unittest2
import os
import shutil
from threading import Thread
import time

import asyncio

from legion.template import LegionTemplate

TEST_FILES_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'templates')


def _setup_template_value(value_file_name, source_file_name):
    source = os.path.join(TEST_FILES_LOCATION, source_file_name)
    target = os.path.join(TEST_FILES_LOCATION, value_file_name)

    shutil.copyfile(source, target)


class TestLegionTemplate(unittest2.TestCase):
    """
    Unit tests for template system
    """
    SLEEP_INTERVAL_IN_SEC = 3

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def assertStringEqualToTemplateFile(self, expected_string, template_file, msg=None):
        template_file_path = os.path.join(TEST_FILES_LOCATION, template_file)
        with open(template_file_path, 'r') as file_stream:
            content = file_stream.read().strip('\n\r ')
            expected_string = expected_string.strip('\n\r ')
            self.assertEqual(content, expected_string, msg)

    def test_empty_template(self):
        """
        Test exception generation for empty template file
        """
        with TemplateRenderThread('yaml_file_empty.t', 'yaml_file_empty.tmp.out') as renderer:
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
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
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            self.assertStringEqualToTemplateFile(renderer.output_data, 'yaml_file_test_values_expected_1.out')

            # Set updated data
            print('Updating file..')
            _setup_template_value('yaml_file_test_values.tmp.yml', 'yaml_file_test_values_2.yml')
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            self.assertStringEqualToTemplateFile(renderer.output_data, 'yaml_file_test_values_expected_2.out')

    def test_duo_yaml_files_watch(self):
        """
        Test duo yaml files watch module
        """
        # Set initial data
        _setup_template_value('yaml_file_test_values_first.tmp.yml', 'yaml_file_test_values_1.yml')
        _setup_template_value('yaml_file_test_values_second.tmp.yml', 'yaml_file_test_values_2.yml')

        with TemplateRenderThread('yaml_file_test_duo.t', 'yaml_file_test_duo.tmp.out') as renderer:
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            self.assertStringEqualToTemplateFile(renderer.output_data, 'yaml_file_test_duo_expected_1.out')

            # Set updated data
            print('Updating first file..')
            _setup_template_value('yaml_file_test_values_first.tmp.yml', 'yaml_file_test_values_2.yml')
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            self.assertStringEqualToTemplateFile(renderer.output_data, 'yaml_file_test_duo_expected_2.out')

            # Set updated data
            print('Updating second file..')
            _setup_template_value('yaml_file_test_values_second.tmp.yml', 'yaml_file_test_values_1.yml')
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            self.assertStringEqualToTemplateFile(renderer.output_data, 'yaml_file_test_duo_expected_3.out')


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
            template_system = LegionTemplate(self.template_path, self.output_path)
            template_system.render_loop()
        except Exception as exception:
            self.raised_exception = exception
            raise self.raised_exception

    def __enter__(self):
        """
        A function of Context manager, which starts a thread with a render loop.

        :return: None
        """
        self.start()
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

        :return: None
        """
        with open(self.output_path, 'r') as file:
            return file.read()


if __name__ == '__main__':
    unittest2.main()
