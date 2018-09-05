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
            context.copy_model('summation_model')
            model_id, model_version, model_file, _ = context.execute_model()
            self.assertEqual(model_id, 'test-summation', 'incorrect model id')
            self.assertEqual(model_version, '1.0', 'incorrect model version')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'default': {
                        'input_params': False,
                        'name': 'default',
                        'use_df': False,
                    }
                },
                'model_id': model_id,
                'model_version': model_version
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

    def test_math_model_build_and_query_with_multiple_endpoints(self):
        with ModelDockerBuilderContainerContext() as context:
            context.copy_model('math_model')
            model_id, model_version, model_file, _ = context.execute_model()
            self.assertEqual(model_id, 'test-math', 'incorrect model id')
            self.assertEqual(model_version, '1.0', 'incorrect model version')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'sum': {
                        'input_params': False,
                        'name': 'sum',
                        'use_df': False,
                    },
                    'mul': {
                        'input_params': False,
                        'name': 'mul',
                        'use_df': False,
                    }
                },
                'model_id': model_id,
                'model_version': model_version
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(a=10, b=20, endpoint='sum')['result'], 30,
                             'invalid invocation result')
            self.assertEqual(context.client.invoke(a=40, b=2, endpoint='mul')['result'], 80,
                             'invalid invocation result')
            self.assertListEqual(
                context.client.batch([{'a': 10, 'b': 10}, {'a': 20, 'b': 30}], endpoint='sum'),
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
            self.assertListEqual(
                context.client.batch([{'a': 2, 'b': 15}, {'a': 1, 'b': 20}], endpoint='mul'),
                [
                    {
                        'result': 30,
                    },
                    {
                        'result': 20,
                    }
                ],
                'invalid batch invocation result'
            )

    def test_complex_model_build_and_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.copy_model('complex_model')
            model_id, model_version, model_file, _ = context.execute_model()
            self.assertEqual(model_id, 'complex', 'incorrect model id')
            self.assertEqual(model_version, '1.0', 'incorrect model version')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'default': {
                        'input_params': False,
                        'name': 'default',
                        'use_df': False,
                    }
                },
                'model_id': model_id,
                'model_version': model_version
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
            context.copy_model('model_with_io_operations')
            model_id, model_version, model_file, _ = context.execute_model()
            self.assertEqual(model_id, 'io-model', 'incorrect model id')
            self.assertEqual(model_version, '1.0', 'incorrect model version')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'default': {
                        'input_params': False,
                        'name': 'default',
                        'use_df': False,
                    }
                },
                'model_id': model_id,
                'model_version': model_version
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(value=20)['result'], 62, 'invalid invocation result')

    def test_native_model_build_and_simple_query(self):
        with ModelDockerBuilderContainerContext() as context:
            context.copy_model('model_with_native')
            model_id, model_version, model_file, _ = context.execute_model()
            self.assertEqual(model_id, 'native-model', 'incorrect model id')
            self.assertEqual(model_version, '1.0', 'incorrect model version')
            image_id, _ = context.build_model_container(model_file)

        with ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'default': {
                        'input_params': False,
                        'name': 'default',
                        'use_df': False,
                    },
                },
                'model_id': model_id,
                'model_version': model_version
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(x=1)['code'], 0, 'invalid invocation result')


if __name__ == '__main__':
    unittest2.main()
