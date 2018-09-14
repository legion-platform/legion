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
import legion.utils as utils

import unittest2


class TestUtilsOther(unittest2.TestCase):
    def test_lambda_analyzing(self):
        lamb = lambda x: x**2  # pylint: disable=E731
        description = utils.get_function_description(lamb)
        self.assertIn('function <lambda>', description)
        self.assertIn(__file__, description)

    def test_function_analyzing(self):
        def tmp():
            return 42
        description = utils.get_function_description(tmp)
        self.assertIn('function tmp', description)
        self.assertIn(__file__, description)

    def test_non_callable_analyzing(self):
        tmp = 42
        description = utils.get_function_description(tmp)
        self.assertIn('not callable object', description)

    def test_ensure_retries_positive(self):
        counter = 0

        def func():
            nonlocal counter
            if counter > 1:
                return 42
            counter += 1

        result = utils.ensure_function_succeed(func, 3, 1)
        self.assertEqual(result, 42)
        self.assertEqual(counter, 2)

    def test_ensure_retries_negative(self):
        counter = 0

        def func():
            nonlocal counter
            if counter > 1:
                return 42
            counter += 1

        result = utils.ensure_function_succeed(func, 2, 1)
        self.assertEqual(result, None)
        self.assertEqual(counter, 2)


if __name__ == '__main__':
    unittest2.main()
