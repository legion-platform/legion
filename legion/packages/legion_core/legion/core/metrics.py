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
import socket
import logging
import time
from enum import Enum

import legion.core.config
from legion.core.utils import normalize_name


LOGGER = logging.getLogger(__name__)


class Metric(Enum):
    """
    Metric type
    """

    TRAINING_ACCURACY = 'training-accuracy'
    TEST_ACCURACY = 'test-accuracy'
    TRAINING_LOSS = 'training-loss'


def is_metrics_enabled():
    """
    Get is sending of metrics is enabled

    :return: bool -- is sending of metrics is enabled or not
    """
    return legion.config.MODEL_TRAIN_METRICS_ENABLED


def get_metric_endpoint():
    """
    Get metric endpoint

    :return: metric server endpoint
    """
    host = legion.config.GRAPHITE_HOST
    port = legion.config.GRAPHITE_PORT
    namespace = legion.config.GRAPHITE_NAMESPACE
    return host, port, namespace


def get_build_number():
    """
    Get current build number

    :return: int -- build number
    """
    try:
        return legion.config.BUILD_NUMBER
    except ValueError:
        raise Exception('Cannot parse build number as integer')


def get_metric_name(metric, model_id):
    """
    Get metric name on stats server

    :param metric: instance of Metric or custom name
    :type metric: :py:class:`legion.metrics.Metric` or str
    :param model_id: model ID
    :type model_id: str
    :return: str -- metric name on stats server
    """
    name = metric.value if isinstance(metric, Metric) else str(metric)
    return normalize_name('{}.metrics.{}'.format(model_id, name))


def get_build_metric_name(model_id):
    """
    Get build # name on stats server

    :param model_id: model ID
    :type model_id: str
    :return: str -- build # name on stats server
    """
    return '{}.metrics.build'.format(model_id)


def send_udp(host, port, message):
    """
    Send message with UDP

    :param host: target host
    :type host: str
    :param port: target port
    :type port: int
    :param message: data string or bytes
    :type message: str or bytes
    :return: None
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if isinstance(message, str):
        message = message.encode('utf-8')

    sock.sendto(message, (host, port))


def send_tcp(host, port, message):
    """
    Send message with TCP

    :param host: target host
    :type host: str
    :param port: target port
    :type port: int
    :param message: data string or bytes
    :type message: str or bytes
    :return: None
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    if isinstance(message, str):
        message = message.encode('utf-8')

    sock.send(message)
    sock.close()


def send_metric(model_id, metric, value):
    """
    Send build metric value

    :param model_id: model ID
    :type model_id: str
    :param metric: metric type or metric name
    :type metric: :py:class:`legion.metrics.Metric` or str
    :param value: metric value
    :type value: float or int
    :return: None
    """
    if not is_metrics_enabled():
        LOGGER.warning('Sending of metric {!r} with value {!r} has been ignored'.format(metric, value))
        return

    host, port, namespace = get_metric_endpoint()

    metric_name = '{}.{}'.format(namespace, get_metric_name(metric, model_id))
    message = "{} {} {}\n".format(metric_name, float(value), int(time.time()))
    send_tcp(host, port, message)

    build_no = get_build_number()
    metric_name = '{}.{}'.format(namespace, get_metric_name('build', model_id))
    message = "{} {} {}\n".format(metric_name, build_no, int(time.time()))
    send_tcp(host, port, message)
