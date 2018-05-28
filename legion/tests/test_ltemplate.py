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

import unittest2
import tempfile
import os
from threading import Thread
import time
import asyncio
from legion.templating import TemplateSystem
import yaml


class TestTemplateSystem(unittest2.TestCase):
    """
    Unit tests for template system
    """

    TEMPLATE_LINE = '<file>%s</file>'

    LOAD_MODULE_LINE = "{{ load_module('legion.io.render_on_file_change', filepath='%s', var_name='data') }}"
    TEMPLATE_PRINT_VARIABLE = "{{ data }}"

    LOAD_YAML_MODULE_LINE = "{{ load_module('legion.io.render_on_file_change', filepath='%s', " \
                            "var_name='data', is_yaml_file=True) }}"
    TEMPLATE_PRINT_YAML_VARIABLE = '{{ data["item"] }}'

    SLEEP_INTERVAL_IN_SEC = 3

    def setUp(self):
        """
        Set up test data
        """
        self.random_data = str(time.time())  # create random string
        self.output_file, self.output_path = tempfile.mkstemp()  # temp output file for file watch
        self.input_file, self.input_path = tempfile.mkstemp()  # temp input file for file watch
        self.template_file, self.template_path = tempfile.mkstemp()  # temp template file for file watch

        with os.fdopen(self.template_file, 'w') as template:  # create template file for file watch
            template.write(self.LOAD_MODULE_LINE % self.input_path)
            template.write(self.TEMPLATE_LINE % self.TEMPLATE_PRINT_VARIABLE)

        self.output_yaml_file, self.output_yaml_path = tempfile.mkstemp()  # temp output file for yaml file watch
        self.input_yaml_file, self.input_yaml_path = tempfile.mkstemp()  # temp input file for yaml file watch
        self.template_yaml_file, self.template_yaml_path = tempfile.mkstemp()  # temp template file for yaml file watch

        with os.fdopen(self.template_yaml_file, 'w') as template:  # create template file for yaml file watch
            template.write(self.LOAD_YAML_MODULE_LINE % self.input_yaml_path)
            template.write(self.TEMPLATE_LINE % self.TEMPLATE_PRINT_YAML_VARIABLE)

    def test_file_watch(self):
        """
        Test a file watch module
        """
        with TemplateRenderThread(self.template_path, self.output_path):
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            with open(self.output_path) as out_file:  # check if output file has empty value
                self.assertEqual(out_file.read(), self.TEMPLATE_LINE % '',
                                 'Output file should contain empty data variable')

            with open(self.input_path, 'w') as data_file:  # write random string to the data file
                data_file.write(self.random_data)

            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            with open(self.output_path) as out_file:  # check if output file has random value
                self.assertEqual(out_file.read(), self.TEMPLATE_LINE % self.random_data,
                                 'Output file should contain same data[item] variable')

    def test_yaml_file_watch(self):
        """
        Test a yaml file watch module
        """
        with TemplateRenderThread(self.template_yaml_path, self.output_yaml_path):
            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            with open(self.output_yaml_path) as out_file:  # check if output file has empty value
                self.assertEqual(out_file.read(), self.TEMPLATE_LINE % '',
                                 'Output file should contain empty data variable')

            with open(self.input_yaml_path, 'w') as data_file:  # write random yaml to the data file
                data_file.write(yaml.dump({'item': self.random_data}))

            time.sleep(self.SLEEP_INTERVAL_IN_SEC)
            with open(self.output_yaml_path) as out_file:  # check if output file has random value from yaml
                self.assertEqual(out_file.read(), self.TEMPLATE_LINE % self.random_data,
                                 'Output file should contain same data variable')


class TemplateRenderThread(Thread):
    """
    A thread with a render loop for file watch test.
    """
    def __init__(self, template_path, output_path):
        """
        Init a Thread object.
        :param template_path: a path to a template file
        :rtype template_path: str
        :param output_path: a path to an output file
        :rtype output_path: str
        """
        Thread.__init__(self)
        self.name = 'template_render_loop'
        self.daemon = True
        self.template_path = template_path
        self.output_path = output_path
        self.event_loop = None

    def run(self):
        """
        Run a render loop for file watch test.
        """
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        template_system = TemplateSystem(self.template_path, self.output_path)
        template_system.render_loop()

    def __enter__(self):
        """
        A function of Context manager, which starts a thread with a render loop.
        """
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        A function of Context manager, which stops an event loop of a thread.
        """
        self.event_loop.stop()
