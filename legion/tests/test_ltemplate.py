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
import _thread
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
    TEMPLATE_PRINT_YAML_VARIABLE = '{% if data is defined %}{{ data["item"] }}{% endif %}'

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

    def _template_render_loop(self):
        """
        Start a thread with a render loop for file watch test
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ts = TemplateSystem(self.template_path, self.output_path)
        ts.render_loop()

    def test_file_watch(self):
        """
        Test a file watch module
        """
        th = _thread.start_new_thread(self._template_render_loop, ())  # start a thread
        time.sleep(self.SLEEP_INTERVAL_IN_SEC)
        with open(self.output_path) as out_file:  # check if output file has empty value
            self.assertEqual(out_file.read(), self.TEMPLATE_LINE % '', 'Output file should contain empty data variable')

        with open(self.input_path, 'w') as data_file:  # write random string to the data file
            data_file.write(self.random_data)

        time.sleep(self.SLEEP_INTERVAL_IN_SEC)
        with open(self.output_path) as out_file:  # check if output file has random value
            self.assertEqual(out_file.read(), self.TEMPLATE_LINE % self.random_data,
                             'Output file should contain same data[item] variable')

    def _yaml_template_render_loop(self):
        """
        Start a thread with a render loop for yaml file watch test
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ts = TemplateSystem(self.template_yaml_path, self.output_yaml_path)
        ts.render_loop()

    def test_yaml_file_watch(self):
        """
        Test a yaml file watch module
        """
        th = _thread.start_new_thread(self._yaml_template_render_loop, ())  # start a thread
        time.sleep(self.SLEEP_INTERVAL_IN_SEC)
        with open(self.output_yaml_path) as out_file:  # check if output file has empty value
            self.assertEqual(out_file.read(), self.TEMPLATE_LINE % '', 'Output file should contain empty data variable')

        with open(self.input_yaml_path, 'w') as data_file:  # write random yaml to the data file
            data_file.write(yaml.dump({'item': self.random_data}))

        time.sleep(self.SLEEP_INTERVAL_IN_SEC)
        with open(self.output_yaml_path) as out_file:  # check if output file has random value from yaml
            self.assertEqual(out_file.read(), self.TEMPLATE_LINE % self.random_data,
                             'Output file should contain same data variable')
