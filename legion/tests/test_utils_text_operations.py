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


class TestUtilsTextOperations(unittest2.TestCase):
    def test_string_to_bool(self):
        examples = (
            ('true', True),
            ('yes', True),
            ('1', True),
            ('t', True),
            ('y', True),
            ('false', False),
            ('no!', False),
            ('not', False),
            ('not a command', False),
        )

        for example, valid_answer in examples:
            self.assertEqual(utils.string_to_bool(example), valid_answer)

    def test_string_to_bool_from_bool(self):
        examples = (
            (True, True),
            (False, False),
        )

        for example, valid_answer in examples:
            self.assertEqual(utils.string_to_bool(example), valid_answer)


if __name__ == '__main__':
    unittest2.main()
