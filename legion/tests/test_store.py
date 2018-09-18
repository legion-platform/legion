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
from __future__ import print_function
import logging
import unittest2

import legion.model
import legion.pymodel.store

import dill


class TestStore(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

    @unittest2.skip
    def test_base_store(self):
        store = legion.pymodel.store.SharedStore()
        store.a = 415616
        self.assertEqual(store.a, 415616)

    def test_copy_store(self):
        store = legion.pymodel.store.SharedStore()
        store.a = 415617
        store_b = dill.copy(store)
        self.assertEqual(repr(store_b._id), repr(store._id))


if __name__ == '__main__':
    unittest2.main()
