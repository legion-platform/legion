from __future__ import print_function

import os
import unittest2

import drun.grafana as grafana


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        host = os.environ.get('GRAFANA_URL', 'http://grafana:3000/')
        user = os.environ.get('GRAFANA_USER', 'admin')
        password = os.environ.get('GRAFANA_PASSWORD', 'admin')
        self.client = grafana.GrafanaClient(host, user, password)

    def test_dashboard_creation(self):
        model_id = 'test_grafana'
        if self.client.is_dashboard_exists(model_id):
            self.client.remove_dashboard_for_model(model_id)

        self.client.create_dashboard_for_model(model_id, '2.0')

        self.assertTrue(self.client.is_dashboard_exists(model_id))


if __name__ == '__main__':
    unittest2.main()
