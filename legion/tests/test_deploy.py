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
import os
import sys
import logging

import legion.config
import legion.containers.docker
import legion.io
import legion.model.client
import legion.model.model_id

import unittest2

# Extend PYTHONPATH in order to import test tools and models
sys.path.extend(os.path.dirname(__file__))

from legion_test_utils import ModelLocalContainerExecutionContext, build_distribution, \
    ModelDockerBuilderContainerContext


class TestDeploy(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)
        build_distribution()

    def test_summation_model_build_and_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.prepare_workspace()
            context.copy_model('summation_model')
            model_id, model_version, model_file, _ = context.execute_model('summation_model')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'input_params': False,
                'use_df': False,
                'version': '1.0'
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(a=10, b=20)['result'], 30, 'invalid invocation result')
            self.assertListEqual(
                context.client.batch([{'a': 10, 'b': 10}, {'a': 20, 'b': 30}]),
                [
                    {
                        'result': 20,
                    },
                    {
                        'result': 50,
                    }
                ],
                'invalid batch invocation result'
            )

    def test_complex_model_build_and_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.prepare_workspace()
            context.copy_model('complex_model')
            context.copy_model_directory('complex_package')
            model_id, model_version, model_file, _ = context.execute_model('complex_model')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'input_params': False,
                'use_df': False,
                'version': '1.0'
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(value=20)['result'], 62, 'invalid invocation result')
            self.assertListEqual(
                context.client.batch([{'value': 1}, {'value': 100}]),
                [
                    {
                        'result': 43,
                    },
                    {
                        'result': 142,
                    }
                ],
                'invalid batch invocation result'
            )

    def test_io_model_build_and_simple_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.prepare_workspace()
            context.copy_model('model_with_io_operations')
            model_id, model_version, model_file, _ = context.execute_model('model_with_io_operations')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'input_params': False,
                'use_df': False,
                'version': '1.0'
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(value=20)['result'], 62, 'invalid invocation result')

    def test_native_model_build_and_simple_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.prepare_workspace()
            context.copy_model('model_with_native')
            model_id, model_version, model_file, _ = context.execute_model('model_with_native')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'input_params': False,
                'use_df': False,
                'version': '1.0'
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(x=1)['code'], 0, 'invalid invocation result')


if __name__ == '__main__':
    unittest2.main()
