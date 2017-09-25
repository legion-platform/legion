import unittest2
import drun.model
import pandas
import numpy


class TestScipyModel(unittest2.TestCase):

    def test_positive(self):
        def prepare(x):
            x['additional'] = x['d_int']
            return x

        def apply(x):
            assert type(x) == pandas.DataFrame

            assert x['d_int'].dtype == numpy.int
            assert x['d_float'].dtype == numpy.float
            assert x['d_str'].dtype in [numpy.str, numpy.object]
            assert x['additional'].dtype == numpy.int

        s = drun.model.ScipyModel(
            apply,
            prepare,
            {'d_int': numpy.int, 'd_float': numpy.float, 'd_str': numpy.str},
            version='1.0')

        s.apply({'d_int': '1', 'd_float': '2.0', 'd_str': 'omg'})

    def test_typecast(self):
        s = drun.model.ScipyModel(
            lambda x: {'result': 42},
            lambda x: x,
            column_types={'d_int': numpy.int, 'd_float': numpy.float, 'd_str': numpy.str, 'excessive': numpy.object},
            version='1.0')

        s.apply({'d_int': '1', 'd_float': '2.0', 'd_str': 'omg'})

        print(s.description())

if __name__ == '__main__':
    unittest2.main()
