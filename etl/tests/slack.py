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
Unit test for slack package.
"""

import unittest
from etl.slack import notification


class TestNotification(unittest.TestCase):

    def test_remove_tags(self):
        cases = [
            {
                "html": "<h1> Hello </h1>",
                "plain_text": " Hello "
            }, {
                "html": "if i<1 and i>0:",
                "plain_text": "if i0:"
            }
        ]
        for case in cases:
            self.assertEqual(notification.remove_tags(case["html"]), case["plain_text"])


if __name__ == '__main__':
    unittest.main()
