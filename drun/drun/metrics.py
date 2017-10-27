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
"""
Model metrics
"""
import os
from enum import Enum

import drun.env

import statsd


class Metric(Enum):
    """
    Metric type
    """

    TRAINING_ACCURACY = 'training_accuracy'
    TEST_ACCURACY = 'test_accuracy'
    TRAINING_LOSS = 'training_loss'


_server_connection = None
_model_name = None


def get_metric_endpoint():
    """
    Get metric endpoint

    :return: metric server endpoint
    """
    host = os.getenv(*drun.env.STATSD_HOST)
    port = int(os.getenv(*drun.env.STATSD_PORT))
    namespace = os.getenv(*drun.env.STATSD_NAMESPACE)
    return host, port, namespace


def get_build_number():
    """
    Get current build number

    :return: int -- build number
    """
    try:
        return int(os.getenv(*drun.env.BUILD_NUMBER))
    except ValueError:
        raise Exception('Cannot parse build number as integer')


def get_metric_name(metric):
    """
    Get metric name on stats server

    :param metric: metric
    :type metric: :py:class:`drun.metrics.Metric`
    :return: str -- metric name on stats server
    """
    return '%s.metrics.%s' % (_model_name, metric.value)


def get_build_metric_name():
    """
    Get build # name on stats server

    :return: str -- build # name on stats server
    """
    return '%s.metrics.build' % _model_name


def send_metric(metric, value):
    """
    Send metric value

    :param metric: metric type
    :type metric: :py:class:`drun.metrics.Metric`
    :param value: metric value
    :type value: float or int
    :return: None
    """
    _connect_to_server()
    _server_connection.incr(get_metric_name(metric), value)


def _connect_to_server():
    """
    Connect to metrics server if not yet connected

    :return: None
    """
    global _server_connection
    if _server_connection:
        return

    host, port, namespace = get_metric_endpoint()
    _server_connection = statsd.StatsClient(host, port, prefix=namespace)


def init_metric(model_name):
    """
    Init metrics

    :param model_name: model name
    :type model_name: str
    :return: None
    """
    global _model_name
    _model_name = model_name


def get_model_name():
    """
    Get current model name

    :return: str or None
    """
    return _model_name


def reset():
    """
    Reset model name and connection

    :return: None
    """
    global _model_name
    global _server_connection
    _model_name = None
    _server_connection = None
