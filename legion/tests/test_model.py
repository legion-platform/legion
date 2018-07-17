#
#    Copyright 2018 EPAM Systems
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
Test models
"""

import legion.io
import legion.model
import legion.model.types as types
import numpy
import pandas
import unittest2


class TestScipyModel(unittest2.TestCase):
    """
    Unit tests for models
    """

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

        df = pandas.DataFrame([{
            'd_int': 1,
            'd_float': 1.0,
            'd_str': 'what?'
        }])

        s = legion.model.model.ScipyModel(
            apply,
            prepare,
            legion.io._get_column_types(df),
            version='1.0')

        s.apply({'d_int': '1', 'd_float': '2.0', 'd_str': 'omg'})

    def test_typecast(self):

        df = pandas.DataFrame([{
            'd_int': 1,
            'd_float': 1.0,
            'd_str': 'what?',
            'excessive': False
        }])

        class CustomBoolObject(types.BaseType):
            def __init__(self):
                super(CustomBoolObject, self).__init__(default_numpy_type=numpy.bool_)

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

        def apply(x):
            assert type(x) == pandas.DataFrame

            assert x['d_int'].dtype == numpy.int
            assert x['d_float'].dtype == numpy.float
            assert x['d_str'].dtype in [numpy.str, numpy.object]
            assert x['excessive'].dtype == numpy.bool_

        s = legion.model.model.ScipyModel(
            apply,
            lambda x: x,
            column_types=legion.io._get_column_types((df, {'excessive': CustomBoolObject()})),
            version='1.0')

        s.apply({'d_int': '1', 'd_float': '2.0', 'd_str': 'omg', 'excessive': 'of course'})
        print(s.description)


if __name__ == '__main__':
    unittest2.main()
