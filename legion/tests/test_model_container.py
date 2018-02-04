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

import os

import legion.io
import legion.model
import legion.model.model_id
import legion.model.types
import numpy
import pandas
import unittest2


class TestModelContainer(unittest2.TestCase):
    def test_model_pack_unpack(self):
        def prepare(x):
            x['additional'] = x['d_int']
            return x

        def apply(x):
            assert type(x) == pandas.DataFrame

            assert x['d_int'].dtype == numpy.int
            assert x['d_float'].dtype == numpy.float

        df = pandas.DataFrame([{
            'd_int': 1,
            'd_float': 1.0,
        }])

        version = '1.3'
        path = 'test.model'
        model_id = 'demo_model'

        try:
            legion.model.model_id.init(model_id)
            legion.io.export(path,
                             apply,
                             prepare,
                             input_data_frame=df,
                             version=version)

            self.assertTrue(os.path.exists(path), 'File not exists')

            with legion.io.ModelContainer(path) as container:
                self.assertTrue('model.id' in container, 'Property `model.id` is not set')
                self.assertTrue('model.version' in container, 'Property `model.version` is not set')
                self.assertEqual(container['model.version'], version, 'Undefined version of model')
                self.assertEqual(container['model.id'], model_id, 'Undefined id of model')
                self.assertEqual(container.model.prepare_func({'d_int': 10})['additional'], 10, 'Model check failed')

                self.assertIsInstance(container.model.column_types, dict, 'Column types dict is not dict')
                random_column = container.model.column_types[list(container.model.column_types.keys())[0]]
                self.assertIsInstance(random_column, legion.model.types.ColumnInformation,
                                      'Random column is not ColumnInf.')

        finally:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == '__main__':
    unittest2.main()
