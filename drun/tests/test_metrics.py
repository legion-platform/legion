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

import os
import time
import unittest2
from unittest.mock import patch

import drun.metrics as metrics
import drun.model_id
import drun.env as env


def _reset_model_id():
    drun.model_id._model_id = None
    drun.model_id._model_initialized_from_function = False
    if env.MODEL_ID[0] in os.environ:
        os.unsetenv(env.MODEL_ID[0])
        del os.environ[env.MODEL_ID[0]]


class MetricContent:
    def __init__(self, model, build, init_at_startup=True):
        self._model = model
        self._build = build
        self._old_build_number_env = os.getenv(*env.BUILD_NUMBER)
        self._init_at_startup = init_at_startup

    def __enter__(self):
        if self._init_at_startup:
            drun.model_id.init(self._model)
        os.environ[env.BUILD_NUMBER[0]] = str(self._build)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _reset_model_id()
        os.environ[env.BUILD_NUMBER[0]] = str(self._old_build_number_env)


class TestMetrics(unittest2.TestCase):

    def setUp(self):
        _reset_model_id()

    def tearDown(self):
        _reset_model_id()

    def test_metrics_name_building(self):
        model_id = 'demo'
        build_number = 3
        metric = metrics.Metric.TEST_ACCURACY
        with MetricContent(model_id, build_number):
            metrics_name = metrics.get_metric_name(metric)
            self.assertEqual(metrics_name, '%s.metrics.%s' % (model_id, metric.value))

    def test_metrics_get_build_number(self):
        model_id = 'demo'
        build_number = 10
        with MetricContent(model_id, build_number):
            self.assertEqual(metrics.get_build_number(), build_number)

    def test_model_id_deduction_exception(self):
        self.assertEqual(drun.model_id._model_id, None, 'Model ID not empty')
        self.assertEqual(os.getenv(*env.MODEL_ID), None, 'Model ID ENV not empty')
        with self.assertRaises(Exception) as context:
            metrics.send_metric(metrics.Metric.TEST_ACCURACY, 30.0)

    def test_metrics_send(self):
        model_id = 'demo'
        build_number = 10
        metric = metrics.Metric.TEST_ACCURACY
        value = 30.0
        host, port, namespace = metrics.get_metric_endpoint()
        os.environ[env.MODEL_ID[0]] = str(model_id)
        with patch('drun.model_id.send_model_id') as send_model_id_mock:
            with MetricContent(model_id, build_number, init_at_startup=False):
                self.assertEqual(len(send_model_id_mock.call_args_list), 0)
                with patch('drun.metrics.send_tcp') as send_tcp_mock:
                    timestamp = int(time.time())
                    metrics.send_metric(metric, value)

                    self.assertEqual(len(send_model_id_mock.call_args_list), 1)
                    del os.environ[env.MODEL_ID[0]]

                    self.assertTrue(len(send_tcp_mock.call_args_list) == 2, '2 calls founded')
                    for call in send_tcp_mock.call_args_list:
                        self.assertEqual(call[0][0], host)
                        self.assertEqual(call[0][1], port)

                    delimiter = ' '

                    call_with_metric = send_tcp_mock.call_args_list[0][0][2].strip().split(delimiter)
                    call_with_build_number = send_tcp_mock.call_args_list[1][0][2].strip().split(delimiter)

                    self.assertEqual(call_with_metric[0], '%s.%s.metrics.%s' % (namespace, model_id, metric.value))
                    self.assertEqual(float(call_with_metric[1]), value)
                    self.assertEqual(call_with_metric[2], str(timestamp))

                    self.assertEqual(call_with_build_number[0], '%s.%s.metrics.build' % (namespace, model_id))
                    self.assertEqual(int(float(call_with_build_number[1])), build_number)
                    self.assertEqual(call_with_build_number[2], str(timestamp))

    def test_set_model_id_and_reset_metrics(self):
        model_id = 'demo'
        build_number = 10
        old_build_number_env = os.getenv(*env.BUILD_NUMBER)

        _reset_model_id()

        drun.model_id.init(model_id)
        os.environ[env.BUILD_NUMBER[0]] = str(build_number)

        self.assertEqual(metrics.get_model_id(), model_id)
        self.assertEqual(metrics.get_build_number(), build_number)

        _reset_model_id()

        self.assertIsNone(metrics.get_model_id())

        os.environ[env.BUILD_NUMBER[0]] = str(old_build_number_env)

    def test_default_endpoint_detection(self):
        host, port, namespace = metrics.get_metric_endpoint()
        self.assertEqual(host, env.GRAPHITE_HOST[1])
        self.assertEqual(port, env.GRAPHITE_PORT[1])
        self.assertEqual(namespace, env.GRAPHITE_NAMESPACE[1])

    def test_custom_endpoint_detection(self):
        new_host = 'localhost'
        new_port = 1000
        new_namespace = 'tes'

        old_host = os.getenv(*env.GRAPHITE_HOST)
        old_port = os.getenv(*env.GRAPHITE_PORT)
        old_namespace = os.getenv(*env.GRAPHITE_NAMESPACE)

        os.environ[env.GRAPHITE_HOST[0]] = new_host
        os.environ[env.GRAPHITE_PORT[0]] = str(new_port)
        os.environ[env.GRAPHITE_NAMESPACE[0]] = new_namespace

        host, port, namespace = metrics.get_metric_endpoint()
        self.assertEqual(host, new_host)
        self.assertEqual(port, new_port)
        self.assertEqual(namespace, new_namespace)

        if old_host:
            os.environ[env.GRAPHITE_HOST[0]] = old_host
        else:
            os.unsetenv(env.GRAPHITE_HOST[0])

        if old_port:
            os.environ[env.GRAPHITE_PORT[0]] = str(old_port)
        else:
            os.unsetenv(env.GRAPHITE_PORT[0])

        if old_namespace:
            os.environ[env.GRAPHITE_NAMESPACE[0]] = old_namespace
        else:
            os.unsetenv(env.GRAPHITE_NAMESPACE[0])


if __name__ == '__main__':
    unittest2.main()
