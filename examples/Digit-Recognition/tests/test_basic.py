from drun.model_tests import ModelUnitTests
import drun.env
import unittest2
import os


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel(os.environ.get(*drun.env.MODEL_ID))

    def test_nine_decode(self):
        image = self._load_image(os.path.join('files', 'nine.png'))
        response = self._query_model(image=image)
        self.assertEqual(response['digit'], 9)


if __name__ == '__main__':
    unittest2.main()
