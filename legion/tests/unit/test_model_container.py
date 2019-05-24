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
from __future__ import print_function

import logging
import os

import numpy
import pandas
import unittest2
from legion.toolchain import model
from legion.toolchain import types
from legion.toolchain.pymodel.model import Model, ModelEndpoint

LOGGER = logging.getLogger(__name__)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.bin')
MODEL_NAME = 'demo-model'
MODEL_VERSION = '1.3'


class CustomBoolObject(types.BaseType):
    def __init__(self):
        super().__init__(default_numpy_type=numpy.bool_)

    def parse(self, value):
        """
        Parse boolean strings like 'of course', 'not sure'
        :param value:
        :return:
        """
        str_value = value.lower()
        if str_value == 'of course':
            return True
        elif str_value == 'not sure':
            return False
        else:
            raise Exception('Invalid value: %s' % (str_value,))

    def export(self, value):
        return value


def make_square(x):
    if x['are_you_sure']:
        return x['value'] ** 2
    return x['value']


def apply_add(x):
    return x['a'] + x['b']


def apply_sub(x):
    return x['a'] - x['b']


def prepare_pd(x):
    x['additional'] = x['d_int']
    return x


def apply_pd(x):
    assert isinstance(x, pandas.DataFrame)

    assert x['d_int'].dtype == numpy.int
    assert x['d_float'].dtype == numpy.float


df = pandas.DataFrame([{
    'd_int': 1,
    'd_float': 1.0,
}])


class TestModelContainer(unittest2.TestCase):
    @classmethod
    def tearDown(cls):
        if os.path.exists(MODEL_PATH):
            logging.info('Removing {}'.format(MODEL_PATH))
            os.unlink(MODEL_PATH)

        model.reset_context()

    def test_square_with_cast(self):
        model.init(MODEL_NAME, MODEL_VERSION) \
            .export(make_square, {
                    'value': model.int32,
                    'are_you_sure': types.ColumnInformation(CustomBoolObject())
                    }, endpoint='square') \
            .save(MODEL_PATH)

        self.assertTrue(os.path.exists(MODEL_PATH), 'File not exists')

        container = Model.load(MODEL_PATH)
        invoke = container.endpoints['square'].invoke
        self.assertEqual(invoke({'value': 10, 'are_you_sure': 'of course'}), 100)
        self.assertEqual(invoke({'value': 10, 'are_you_sure': 'not sure'}), 10)

    def test_model_pack_native_multiple_endpoints(self):
        model.init(MODEL_NAME, MODEL_VERSION) \
            .export_untyped(apply_add, endpoint='add') \
            .export_untyped(apply_sub, endpoint='sub') \
            .save(MODEL_PATH)

        self.assertTrue(os.path.exists(MODEL_PATH), 'File not exists')

        container = Model.load(MODEL_PATH)

        self.assertEqual(container.model_name, MODEL_NAME, 'invalid model id')
        self.assertEqual(container.model_version, MODEL_VERSION, 'invalid model version')

        endpoints = container.endpoints
        endpoint_names = set(endpoints.keys())
        self.assertSetEqual({'add', 'sub'}, endpoint_names)

        add_endpoint = endpoints['add']
        self.assertIsInstance(add_endpoint, ModelEndpoint)
        self.assertEqual(add_endpoint.name, 'add')
        self.assertEqual(add_endpoint.use_df, False)
        self.assertEqual(add_endpoint.apply({'a': 10, 'b': 32}), 42)

        sub_endpoint = endpoints['sub']
        self.assertIsInstance(sub_endpoint, ModelEndpoint)
        self.assertEqual(sub_endpoint.name, 'sub')
        self.assertEqual(sub_endpoint.use_df, False)
        self.assertEqual(sub_endpoint.apply({'a': 80, 'b': 32}), 48)

    def test_model_pack_with_df_single_endpoint(self):
        model.init(MODEL_NAME, MODEL_VERSION) \
            .export_df(apply_pd, df, prepare_func=prepare_pd) \
            .save(MODEL_PATH)

        self.assertTrue(os.path.exists(MODEL_PATH), 'File not exists')

        container = Model.load(MODEL_PATH)

        self.assertEqual(container.model_name, MODEL_NAME, 'invalid model id')
        self.assertEqual(container.model_version, MODEL_VERSION, 'invalid model version')

        endpoints = container.endpoints
        self.assertIn('default', endpoints.keys())

        endpoint = endpoints['default']

        self.assertIsInstance(endpoint, ModelEndpoint)
        self.assertEqual(endpoint.name, 'default')
        self.assertEqual(endpoint.use_df, True)

        self.assertEqual(endpoint.prepare({'d_int': 10})['additional'], 10, 'Model check failed')

        self.assertIsInstance(endpoint.column_types, dict, 'Column types dict is not dict')
        random_column = endpoint.column_types[list(endpoint.column_types.keys())[0]]
        self.assertIsInstance(random_column, types.ColumnInformation,
                              'Random column is not ColumnInf.')


if __name__ == '__main__':
    unittest2.main()
