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

import base64

from PIL import Image as PYTHON_Image
import pandas as pd
import unittest2

from legion.toolchain import types


class TestTypes(unittest2.TestCase):
    _multiprocess_can_split_ = True

    def assertValidImage(self, obj, width, height):
        if not isinstance(obj, PYTHON_Image.Image):
            raise AssertionError('Object of type %s is not an image' % (type(obj),))

        if width and height and (obj.width != width or obj.height != height):
            raise AssertionError('Image size (%d, %d) not equals to (%d, %d)' %
                                 (obj.width, obj.height, width, height))

    def test_bool_conversions(self):
        self.assertEqual(types.Bool.parse('true'), True)
        self.assertEqual(types.Bool.parse('t'), True)
        self.assertEqual(types.Bool.parse('1'), True)
        self.assertEqual(types.Bool.parse('yes'), True)

        self.assertEqual(types.Bool.parse('false'), False)
        self.assertEqual(types.Bool.parse('f'), False)
        self.assertEqual(types.Bool.parse('0'), False)
        self.assertEqual(types.Bool.parse('no'), False)

        with self.assertRaises(ValueError):
            types.Bool.parse('wrongValue')

    def test_integer_convertsions(self):
        self.assertEqual(types.Integer.parse('12'), 12)
        self.assertEqual(types.Integer.parse('25'), 25)
        self.assertEqual(types.Integer.parse('-025'), -25)

        with self.assertRaises(ValueError):
            types.Integer.parse('12.0')

        with self.assertRaises(ValueError):
            types.Integer.parse('ab')

        with self.assertRaises(ValueError):
            types.Integer.parse('12,0')

    def test_float_conversions(self):
        self.assertAlmostEqual(types.Float.parse('25.1'), 25.1, 0.1)
        self.assertAlmostEqual(types.Float.parse('-25.2'), -25.2, 0.1)

        with self.assertRaises(ValueError):
            types.Float.parse('25,2')

    def test_image_conversions(self):
        self.assertValidImage(types.Image.parse('data:image/gif;base64,R0lGODlhEAAOALMAAOazToeHh0tLS/7LZ'
                                                'v/0jvb29t/f3//Ub//ge8WSLf/rhf/3kdbW1mxsbP//mf///yH5BAAAA'
                                                'AAALAAAAAAQAA4AAARe8L1Ekyky67QZ1hLnjM5UUde0ECwLJoExKcppV'
                                                '0aCcGCmTIHEIUEqjgaORCMxIC6e0CcguWw6aFjsVMkkIr7g77ZKPJjPZq'
                                                'Iyd7sJAgVGoEGv2xsBxqNgYPj/gAwXEQA7'), 16, 14)

        image_source_in_base64 = 'R0lGODlhEAAOALMAAOazToeHh0tLS/7LZ' \
                                 'v/0jvb29t/f3//Ub//ge8WSLf/rhf/3kdbW1mxsbP//mf///yH5BAAAA' \
                                 'AAALAAAAAAQAA4AAARe8L1Ekyky67QZ1hLnjM5UUde0ECwLJoExKcppV' \
                                 '0aCcGCmTIHEIUEqjgaORCMxIC6e0CcguWw6aFjsVMkkIr7g77ZKPJjPZq' \
                                 'Iyd7sJAgVGoEGv2xsBxqNgYPj/gAwXEQA7'

        if len(image_source_in_base64) % 4:
            image_source_in_base64 += '=' * (4 - len(image_source_in_base64) % 4)
        image_source_in_bytes = base64.decodebytes(image_source_in_base64.encode('ascii'))

        self.assertValidImage(types.Image.parse(image_source_in_bytes), 16, 14)

        self.assertValidImage(types.Image.parse('http://placehold.it/120x130&text=image1'), 120, 130)

    def test_type_deduction_base(self):
        df = pd.DataFrame([{'a': 1, 'b': 2.0, 'c': False, 'd': 'Hello'}, {'a': -20, 'b': 3.0, 'c': True, 'd': '!'}])

        deducted_types = types.deduct_types_on_pandas_df(df)

        self.assertSetEqual(set(deducted_types.keys()), {'a', 'b', 'c', 'd'})
        self.assertEqual(deducted_types['a'].representation_type, types.Integer)
        self.assertEqual(deducted_types['b'].representation_type, types.Float)
        self.assertEqual(deducted_types['c'].representation_type, types.Bool)
        self.assertEqual(deducted_types['d'].representation_type, types.String)

    def test_type_deduction_with_image(self):
        img = PYTHON_Image.new('RGB', (128, 20), 'black')
        df = pd.DataFrame([{'a': 1, 'i': img}, {'a': 2, 'i': img}])

        deducted_types = types.deduct_types_on_pandas_df(df)

        self.assertSetEqual(set(deducted_types.keys()), {'a', 'i'})
        self.assertEqual(deducted_types['a'].representation_type, types.Integer)
        self.assertEqual(deducted_types['i'].representation_type, types.Image)

    def test_type_deduction_with_custom(self):
        df = pd.DataFrame([{'a': 1, 's': 'Hello'.encode('ascii')}])

        deducted_types = types.deduct_types_on_pandas_df(df, {'s': types.String})

        self.assertSetEqual(set(deducted_types.keys()), {'a', 's'})
        self.assertEqual(deducted_types['a'].representation_type, types.Integer)
        self.assertEqual(deducted_types['s'].representation_type, types.String)


if __name__ == '__main__':
    unittest2.main()
