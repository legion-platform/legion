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
from legion_airflow.hooks.s3_hook import CsvReader, CsvWriter


class TestCsvReader(unittest.TestCase):

    def test_csv_parsing(self):
        self.assertEqual(CsvReader.read_row('12,23'), ['12', '23'])
        self.assertEqual(CsvReader.read_row('"2""3","56""5""36"'), ['2"3', '56"5"36'])
        self.assertEqual(CsvReader.read_row('"1,30"'), ['1,30'])
        self.assertEqual(CsvReader.read_row(',,23,'), ['', '', '23', ''])
        self.assertEqual(CsvReader.read_row('12;23', column_splitter=';'), ['12', '23'])

    def test_csv_converting(self):
        self.assertEqual(CsvWriter.format_row(['12', '23']), '12,23')
        self.assertEqual(CsvWriter.format_row(['2"3', '56"5"36']), '"2""3","56""5""36"')
        self.assertEqual(CsvWriter.format_row(['1,30']), '"1,30"')
        self.assertEqual(CsvWriter.format_row(['', '', '23', '']), ',,23,')
        self.assertEqual(CsvWriter.format_row(['12', '23'], column_splitter=';'), '12;23')


if __name__ == '__main__':
    unittest.main()
