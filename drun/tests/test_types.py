from __future__ import print_function

import unittest2

import drun.types as types
from PIL import Image as PYTHON_Image


class TestTypes(unittest2.TestCase):
    def assertValidImage(self, object, width, height):
        if not isinstance(object, PYTHON_Image.Image):
            raise AssertionError('Object is not an image')

        if width and height and (object.width != width or object.height != height):
            raise AssertionError('Image size (%d, %d) not equals to (%d, %d)' %
                                 (object.width, object.height, width, height))

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

    def test_image_with_network_loading(self):
        self.assertValidImage(types.Image.parse('http://placehold.it/120x130&text=image1'), 120, 130)


if __name__ == '__main__':
    unittest2.main()
