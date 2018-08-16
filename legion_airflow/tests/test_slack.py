#
#    Copyright 2018 IQVIA
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
from legion_airflow.slack import notification


class TestNotification(unittest.TestCase):

    def test_format_message(self):
        cases = [
            {
                "html": "Try 2 out of 1<br>"
                        "Exception:<br>"
                        "Bash command failed<br>"
                        "Log: <a href='http://google.com'>Link</a><br>"
                        "Host: airflow-company-a-worker-64948cc686-vv826<br>"
                        "Log file: /home/airflow/logs/fail_python_work/sleep_3_seconds/2018-06-11T14:14:00.log<br>"
                        "Mark success: <a href='http://google.com'>Link</a>",
                "slack": "Try 2 out of 1\n"
                         "Exception:\n"
                         "Bash command failed\n"
                         "Log: <http://google.com|Link>\n"
                         "Host: airflow-company-a-worker-64948cc686-vv826\n"
                         "Log file: /home/airflow/logs/fail_python_work/sleep_3_seconds/2018-06-11T14:14:00.log\n"
                         "Mark success: <http://google.com|Link>"
            }
        ]
        for case in cases:
            self.assertEqual(notification.format_message(case["html"]), case["slack"])


if __name__ == '__main__':
    unittest.main()
