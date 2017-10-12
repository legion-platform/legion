from __future__ import print_function

import drun.grafana as grafana
import unittest2


class TestPyserveEndpoints(unittest2.TestCase):

    def setUp(self):
        self.client = grafana.GrafanaClient('http://parallels:80/grafana/', 'admin', 'admin')

    def test_dashboard_creation(self):
        model_id = 'test_grafana'
        if self.client.is_dashboard_exists(model_id):
            self.client.remove_dashboard_for_model(model_id)

        self.client.create_dashboard_for_model(model_id, '2.0')

        self.assertTrue(self.client.is_dashboard_exists(model_id))


if __name__ == '__main__':
    unittest2.main()
