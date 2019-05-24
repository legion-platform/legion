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
import shutil
import sys
import tempfile
import time
import typing
from unittest.mock import patch

import pandas as pd
import unittest2

# Extend PYTHONPATH in order to import test tools and models
from legion.sdk import config
from legion.toolchain import metrics
from legion.toolchain.metrics import send_metric, show_local_metrics

sys.path.extend(os.path.dirname(__file__))
from legion_test_utils import patch_config

MODEL_NAME = 'test-model'


class TestMetrics(unittest2.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self._test_dir = tempfile.mkdtemp()
        self._metric_store = f'{self._test_dir}/.store'
        self.patcher = patch('legion.sdk.config.MODEL_LOCAL_METRIC_STORE', self._metric_store)
        config.MODEL_LOCAL_METRIC_STORE = self.patcher.start()

    def tearDown(self):
        shutil.rmtree(self._test_dir)
        self.patcher.stop()

    def test_metrics_name_building(self):
        metric = metrics.Metric.TEST_ACCURACY
        model_name = 'test-model'
        metrics_name = metrics.get_metric_name(metric, model_name)
        self.assertEqual(metrics_name, '{}.metrics.{}'.format(model_name, metric.value))

    def test_metrics_get_build_number(self):
        build_number = 10
        with patch_config({'BUILD_NUMBER': build_number}):
            self.assertEqual(metrics.get_build_number(), build_number)

    def test_metrics_send(self):
        model_name = 'demo'
        model_version = '1.0'
        build_number = 10
        metric = metrics.Metric.TEST_ACCURACY
        value = 30.0
        timestamp = time.time()
        host, port, namespace = metrics.get_metric_endpoint()

        additional_environment = {
            'BUILD_NUMBER': build_number,
            'MODEL_CLUSTER_TRAIN_METRICS_ENABLED': 'true'
        }

        with patch_config(additional_environment):
            with patch('legion.toolchain.metrics.send_tcp') as send_tcp_mock, patch('time.time',
                                                                                    return_value=timestamp):
                metrics.send_metric(model_name, model_version, metric, value)

                self.assertEqual(1, len(send_tcp_mock.call_args_list), '2 calls have not been founded')
                for call in send_tcp_mock.call_args_list:
                    self.assertEqual(call[0][0], host)
                    self.assertEqual(call[0][1], port)

                passed_metrics: typing.List[str] = send_tcp_mock.call_args_list[0][0][2]
                self.assertEqual(2, len(passed_metrics))

                call_with_metric, call_with_build_number = tuple(passed_metrics)

                self.assertEqual(call_with_metric, f'{namespace}.{model_name}.metrics.{metric.value}:{value}|c')
                self.assertEqual(call_with_build_number, f'{namespace}.{model_name}.metrics.build:{build_number}|c')

    def test_metrics_send_disabled(self):
        model_name = 'demo'
        model_version = '1.0'
        build_number = 10
        metric = metrics.Metric.TEST_ACCURACY
        value = 30.0

        additional_environment = {
            'BUILD_NUMBER': build_number,
            'MODEL_CLUSTER_TRAIN_METRICS_ENABLED': False
        }
        with patch_config(additional_environment):
            with patch('legion.toolchain.metrics.send_tcp') as send_tcp_mock:
                metrics.send_metric(model_name, model_version, metric, value)

                self.assertTrue(len(send_tcp_mock.call_args_list) == 0, '0 calls have not been founded')

    def test_default_endpoint_detection(self):
        host, port, namespace = metrics.get_metric_endpoint()
        self.assertEqual(host, config.METRICS_HOST)
        self.assertEqual(port, config.METRICS_PORT)
        self.assertEqual(namespace, config.NAMESPACE)

    def test_default_is_metrics_enabled(self):
        self.assertFalse(config.MODEL_CLUSTER_TRAIN_METRICS_ENABLED)

    def test_show_local_metrics_empty(self):
        df = show_local_metrics("non-valid-id")
        self.assertTrue(df.empty)

    def test_show_local_metrics_multiple_models(self):
        model_name_1 = "model_name_1"
        model_version_1_1 = "1.0"
        model_version_1_2 = "2.0"

        model_name_2 = "model_name_2"
        model_version_2_1 = "1.0"

        metric_name_1 = "metric-name-1"
        metric_name_2 = "metric-name-2"
        metric_name_3 = "metric-name-3"

        metric_value_1 = 11.0
        metric_value_2 = 22.0
        metric_value_3 = 33.0

        metric_value_2_1 = 111.0
        metric_value_2_2 = 222.0
        metric_value_2_3 = 333.0

        send_metric(model_name_1, model_version_1_1, metric_name_1, metric_value_1)
        send_metric(model_name_1, model_version_1_1, metric_name_2, metric_value_2)
        send_metric(model_name_1, model_version_1_2, metric_name_1, metric_value_1)
        send_metric(model_name_1, model_version_1_2, metric_name_3, metric_value_3)

        metrics_1 = show_local_metrics(model_name_1)
        self.assertFalse(metrics_1.empty)
        self.assertTrue(show_local_metrics(model_name_2).empty)

        # Check that the following dataframe will be returned
        #      Model ID Model Version  metric-name-1  metric-name-2  metric-name-3
        # 0  model_name_1           1.0           11.0           22.0            NaN
        # 1  model_name_1           2.0           11.0            NaN           33.0
        self.assertEqual(2, len(list(metrics_1.iterrows())))
        for metric in metrics_1.iterrows():
            series = metric[1]
            self.assertEqual(model_name_1, series[0])

            model_version = series[1]
            if model_version_1_1 == model_version:
                # Check metric values of "1.0" version
                self.assertEqual(metric_value_1, series[3])
                self.assertEqual(metric_value_2, series[4])
                self.assertTrue(pd.isna(series[5]))
            elif model_version_1_2 == model_version:
                # Check metric values of "2.0" version
                self.assertEqual(metric_value_1, series[3])
                self.assertTrue(pd.isna(series[4]))
                self.assertEqual(metric_value_3, series[5])

        send_metric(model_name_2, model_version_2_1, metric_name_1, metric_value_2_1)
        send_metric(model_name_2, model_version_2_1, metric_name_2, metric_value_2_2)
        send_metric(model_name_2, model_version_2_1, metric_name_3, metric_value_2_3)

        metrics_df_2 = show_local_metrics(model_name_2)

        print(metrics_df_2.to_string(columns=["Model Name", "Model Version", metric_name_1, metric_name_2,
                                              metric_name_3]))
        self.assertFalse(metrics_df_2.empty)
        self.assertFalse(show_local_metrics(model_name_1).empty)

        # Check that the following dataframe will be returned
        #      Model ID Model Version  metric-name-1  metric-name-2  metric-name-3
        # 0  model_name_2           1.0          111.0          222.0          333.0
        self.assertEqual(1, len(list(metrics_df_2.iterrows())))

        metrics_series_2 = next(metrics_df_2.iterrows())[1]
        self.assertEqual(model_name_2, metrics_series_2[0])
        self.assertEqual(model_version_2_1, metrics_series_2[1])
        self.assertEqual(metric_value_2_1, metrics_series_2[3])
        self.assertEqual(metric_value_2_2, metrics_series_2[4])
        self.assertEqual(metric_value_2_3, metrics_series_2[5])

    def test_custom_endpoint_detection(self):
        new_host = 'localhost'
        new_port = 1000
        new_namespace = 'tes'

        additional_environment = {
            'METRICS_HOST': new_host,
            'METRICS_PORT': new_port,
            'NAMESPACE': new_namespace,
            'MODEL_CLUSTER_TRAIN_METRICS_ENABLED': 'true'
        }
        with patch_config(additional_environment):
            host, port, namespace = metrics.get_metric_endpoint()
            self.assertEqual(host, new_host)
            self.assertEqual(port, new_port)
            self.assertEqual(namespace, new_namespace)


if __name__ == '__main__':
    unittest2.main()
