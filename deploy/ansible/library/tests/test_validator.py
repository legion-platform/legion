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
"""
YAML file validator unittests
"""

import unittest2
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from validator import validate

class ValidatorTests(unittest2.TestCase):

    def setUp(self):
        self._input = {
            "a":None,
            "b":None,
            "c": {
                "d":None,
                "e":None
            },
            'f':[{
                'h':None,
            },],
        }
        self._template = {
            "a": None,
            "b": None,
            "c": {
                "d": None,
                "e": None
            },
            'f': [{
                'h': None,
            }, ],
        }


    def test_valid(self):
        self.assertEqual(validate(self._input, self._template), [])


    def test_invalid(self):
        del self._input["a"]
        self.assertEqual(validate(self._input, self._template), ["/a"])


    def test_invalid_recursive(self):
        del self._input["c"]["d"]
        del self._input["f"][0]["h"]
        self.assertEqual(validate(self._input, self._template), ["/c/d", '/f/h'])



if __name__ == "__main__":
    unittest2.main()