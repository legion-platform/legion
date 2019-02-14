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
import sys
import time
from unittest.mock import patch
import unittest2

import legion.config
import legion.metrics as metrics
import legion.model

# Extend PYTHONPATH in order to import test tools and models
sys.path.extend(os.path.dirname(__file__))
from legion_test_utils import patch_config

MODEL_ID = 'test-model'


class TestMetrics(unittest2.TestCase):
    _multiprocess_can_split_ = True

    def test_metrics_name_building(self):
        metric = metrics.Metric.TEST_ACCURACY
        model_id = 'test-model'
        metrics_name = metrics.get_metric_name(metric, model_id)
        self.assertEqual(metrics_name, '{}.metrics.{}'.format(model_id, metric.value))

    def test_metrics_get_build_number(self):
        build_number = 10
        with patch_config({'BUILD_NUMBER': build_number}):
            self.assertEqual(metrics.get_build_number(), build_number)

    def test_metrics_send(self):
        model_id = 'demo'
        build_number = 10
        metric = metrics.Metric.TEST_ACCURACY
        value = 30.0
        timestamp = time.time()
        host, port, namespace = metrics.get_metric_endpoint()

        additional_environment = {
            'BUILD_NUMBER': build_number,
            'MODEL_TRAIN_METRICS_ENABLED': 'true'
        }

        with patch_config(additional_environment):
            with patch('legion.metrics.send_tcp') as send_tcp_mock, patch('time.time', return_value=timestamp):
                timestamp = int(time.time())
                metrics.send_metric(model_id, metric, value)

                self.assertTrue(len(send_tcp_mock.call_args_list) == 2, '2 calls have not been founded')
                for call in send_tcp_mock.call_args_list:
                    self.assertEqual(call[0][0], host)
                    self.assertEqual(call[0][1], port)

                delimiter = ' '

                call_with_metric = send_tcp_mock.call_args_list[0][0][2].strip().split(delimiter)
                call_with_build_number = send_tcp_mock.call_args_list[1][0][2].strip().split(delimiter)

                self.assertEqual(call_with_metric[0], '{}.{}.metrics.{}'.format(namespace, model_id, metric.value))
                self.assertEqual(float(call_with_metric[1]), value)
                self.assertEqual(call_with_metric[2], str(int(timestamp)))

                self.assertEqual(call_with_build_number[0], '{}.{}.metrics.build'.format(namespace, model_id))
                self.assertEqual(int(float(call_with_build_number[1])), build_number)
                self.assertEqual(call_with_build_number[2], str(int(timestamp)))

    def test_metrics_send_disabled(self):
        model_id = 'demo'
        build_number = 10
        metric = metrics.Metric.TEST_ACCURACY
        value = 30.0

        additional_environment = {
            'BUILD_NUMBER': build_number,
            'MODEL_TRAIN_METRICS_ENABLED': False
        }
        with patch_config(additional_environment):
            with patch('legion.metrics.send_tcp') as send_tcp_mock:
                metrics.send_metric(model_id, metric, value)

                self.assertTrue(len(send_tcp_mock.call_args_list) == 0, '0 calls have not been founded')

    def test_default_endpoint_detection(self):
        host, port, namespace = metrics.get_metric_endpoint()
        self.assertEqual(host, legion.config.GRAPHITE_HOST)
        self.assertEqual(port, legion.config.GRAPHITE_PORT)
        self.assertEqual(namespace, legion.config.GRAPHITE_NAMESPACE)

    def test_default_is_metrics_enabled(self):
        is_enabled = metrics.is_metrics_enabled()
        self.assertEqual(is_enabled, legion.config.MODEL_TRAIN_METRICS_ENABLED)

    def test_custom_endpoint_detection(self):
        new_host = 'localhost'
        new_port = 1000
        new_namespace = 'tes'

        additional_environment = {
            'GRAPHITE_HOST': new_host,
            'GRAPHITE_PORT': new_port,
            'GRAPHITE_NAMESPACE': new_namespace,
            'MODEL_TRAIN_METRICS_ENABLED': 'true'
        }
        with patch_config(additional_environment):
            host, port, namespace = metrics.get_metric_endpoint()
            self.assertEqual(host, new_host)
            self.assertEqual(port, new_port)
            self.assertEqual(namespace, new_namespace)


if __name__ == '__main__':
    unittest2.main()
