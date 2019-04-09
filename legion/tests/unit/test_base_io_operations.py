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
import os
import unittest2

from legion.sdk import utils as legion_utils


class TestIOOperations(unittest2.TestCase):
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls):
        cls.data_directory = os.path.join(os.path.dirname(__file__), 'data')
        cls.sample_archive = os.path.join(cls.data_directory, 'sample-archive.zip')

    def test_archive_extractor_in_root_folder(self):
        with legion_utils.extract_archive_item(self.sample_archive, 'example.txt') as temp_file_path:
            with open(temp_file_path, 'r') as temp_file:
                self.assertEqual(temp_file.read(), '1')

    def test_archive_extractor_in_sub_folder(self):
        with legion_utils.extract_archive_item(self.sample_archive, 'subfolder/example2.txt') as temp_file_path:
            with open(temp_file_path, 'r') as temp_file:
                self.assertEqual(temp_file.read(), '2')


if __name__ == '__main__':
    unittest2.main()
