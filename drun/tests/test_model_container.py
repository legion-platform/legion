from __future__ import print_function

import unittest2
import os

import drun.io
import drun.model
import drun.types

import numpy
import pandas


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

        try:
            drun.io.export(path,
                           apply,
                           prepare,
                           df,
                           version=version)

            self.assertTrue(os.path.exists(path), 'File not exists')

            with drun.io.ModelContainer(path) as container:
                self.assertTrue('model.version' in container, 'Property `model.version` is not set')
                self.assertEqual(container['model.version'], version, 'Undefined version of model')
                self.assertEqual(container.model.prepare_func({'d_int': 10})['additional'], 10, 'Model check failed')

                self.assertIsInstance(container.model.column_types, dict, 'Column types dict is not dict')
                random_column = container.model.column_types[list(container.model.column_types.keys())[0]]
                self.assertIsInstance(random_column, drun.types.ColumnInformation, 'Random column is not ColumnInf.')

        finally:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == '__main__':
    unittest2.main()
