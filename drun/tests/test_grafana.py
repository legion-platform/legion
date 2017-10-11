from __future__ import print_function

import unittest2
import json

import drun.external.grafana as grafana


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        self.client = grafana.GrafanaClient('http://parallels/grafana/', 'admin', 'admin')

    def test_dashboard_creation(self):
        self.client.create_dashboard_for_model('test_grafana', '2.0')


if __name__ == '__main__':
    unittest2.main()
