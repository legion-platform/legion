from __future__ import print_function

import unittest2
import logging
import sys
import json
import argparse

import drun.pyserve as pyserve


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        self.app = pyserve.init_application(argparse.Namespace())
        self.app.testing = True
        self.client = self.app.test_client()

    def _parse_json_response(self, response):
        self.assertEqual(response.mimetype, 'application/json', 'Invalid response mimetype')

        data = response.data

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return json.loads(data)

    def test_model_info(self):
        resp = self.client.get('/api/model/dummy-model/info')
        data = self._parse_json_response(resp)

        self.assertDictEqual(data, {'version': 'dummy'})

    def test_model_invoke(self):
        resp = self.client.post('/api/model/dummy-model/invoke', data={
            'result': "It's working!",
            'age': 35
        })
        data = self._parse_json_response(resp)

        self.assertDictEqual(data, {'result': 'It\'s working!'})


if __name__ == '__main__':
    unittest2.main()
