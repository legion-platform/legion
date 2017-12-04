from drun.model_tests import ModelUnitTests
import unittest2
import random


class BasicTest(ModelUnitTests):
    def setUp(self):
        self.setUpModel('test_summation')

    def test_random_sum(self):
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        response = self._query_model(a=a, b=b)

        self.assertEqual(response['result'], a + b)


if __name__ == '__main__':
    unittest2.main()
