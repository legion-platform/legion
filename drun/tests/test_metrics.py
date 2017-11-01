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
import unittest2

import drun.metrics as metrics
import drun.env as env


class MetricContent:
    def __init__(self, model, build):
        self._model = model
        self._build = build
        self._old_build_number_env = os.getenv(*env.BUILD_NUMBER)

    def __enter__(self):
        metrics.init_metric(self._model)
        os.environ[env.BUILD_NUMBER[0]] = str(self._build)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        metrics.reset()
        os.environ[env.BUILD_NUMBER[0]] = str(self._old_build_number_env)


class TestMetrics(unittest2.TestCase):

    def test_metrics_name_building(self):
        model_name = 'demo'
        build_number = 3
        metric = metrics.Metric.TEST_ACCURACY
        with MetricContent(model_name, build_number):
            metrics_name = metrics.get_metric_name(metric)
            self.assertEqual(metrics_name, '%s.metrics.%s' % (model_name, metric.value))

    def test_metrics_get_build_number(self):
        model_name = 'demo'
        build_number = 10
        with MetricContent(model_name, build_number):
            self.assertEqual(metrics.get_build_number(), build_number)

    def test_set_model_name_and_reset_metrics(self):
        model_name = 'demo'
        build_number = 10
        old_build_number_env = os.getenv(*env.BUILD_NUMBER)

        metrics.init_metric(model_name)
        os.environ[env.BUILD_NUMBER[0]] = str(build_number)

        self.assertEqual(metrics.get_model_name(), model_name)
        self.assertEqual(metrics.get_build_number(), build_number)

        metrics.reset()

        self.assertIsNone(metrics.get_model_name())

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
