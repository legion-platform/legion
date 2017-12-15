from drun.model_tests import ModelUnitTests
import drun.env
import unittest2
import random
import os


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel(os.environ.get(*drun.env.MODEL_ID))

    def test_random_sum(self):
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        response = self._query_model(a=a, b=b)

        self.assertEqual(response['result'], a + b)


if __name__ == '__main__':
    unittest2.main()
