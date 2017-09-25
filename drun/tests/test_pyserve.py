from __future__ import print_function

import unittest2
import logging
import sys
import json
import argparse

import drun.pyserve as pyserve


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        self.app = pyserve.init_application(argparse.Namespace())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_model_info(self):
        resp = self.client.get('/api/model/dummy-model/info')

        assert resp.mimetype == 'application/json'

        data = json.loads(resp.data)
        assert data == {'version': 'dummy'}

    def test_model_invoke(self):
        resp = self.client.post('/api/model/dummy-model/invoke', data={
            'result': "It's working!",
            'age': 35
        })

        assert resp.mimetype == 'application/json'

        data = json.loads(resp.data)
        assert data == {'result': "It's working!"}


if __name__ == '__main__':
    unittest2.main()
