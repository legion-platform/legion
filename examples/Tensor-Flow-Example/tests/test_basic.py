from drun.model_tests import ModelUnitTests
import unittest2
import os


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel('tf_recognize')

    def test_nine_decode(self):
        image = self._load_image(os.path.join('files', 'four.png'))
        response = self._query_model(image=image)
        self.assertEqual(response['digit'], 4)


if __name__ == '__main__':
    unittest2.main()
