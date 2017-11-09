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
import re
import socket
import sys
import time
from enum import Enum

import drun.env


class Metric(Enum):
    """
    Metric type
    """

    TRAINING_ACCURACY = 'training_accuracy'
    TEST_ACCURACY = 'test_accuracy'
    TRAINING_LOSS = 'training_loss'


_model_name = None


def get_metric_endpoint():
    """
    Get metric endpoint

    :return: metric server endpoint
    """
    host = os.getenv(*drun.env.GRAPHITE_HOST)
    port = int(os.getenv(*drun.env.GRAPHITE_PORT))
    namespace = os.getenv(*drun.env.GRAPHITE_NAMESPACE)
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

    :param metric: instance of Metric or custom name
    :type metric: :py:class:`drun.metrics.Metric` or str
    :return: str -- metric name on stats server
    """
    name = metric.value if isinstance(metric, Metric) else str(metric)
    return normalize_name('%s.metrics.%s' % (_model_name, name))


def get_build_metric_name():
    """
    Get build # name on stats server

    :return: str -- build # name on stats server
    """
    return '%s.metrics.build' % _model_name


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


def normalize_name(name):
    """
    Normalize name
    :param name: name to normalize
    :type name: str
    :return: str -- normalized name
    """
    name = name.replace(' ', '_')
    return re.sub('[^a-zA-Z0-9\-_\.]', '', name)


def send_metric(metric, value):
    """
    Send metric value

    :param metric: metric type or metric name
    :type metric: :py:class:`drun.metrics.Metric` or str
    :param value: metric value
    :type value: float or int
    :return: None
    """
    host, port, namespace = get_metric_endpoint()

    metric_name = '%s.%s' % (namespace, get_metric_name(metric))
    message = "%s %f %d\n" % (metric_name, float(value), int(time.time()))
    send_tcp(host, port, message)

    build_no = get_build_number()
    metric_name = '%s.%s' % (namespace, get_metric_name('build'))
    message = "%s %f %d\n" % (metric_name, build_no, int(time.time()))
    send_tcp(host, port, message)


def send_model_name(model_name):
    """
    Send information about model name to stderr

    :param model_name: model name
    :type model_name: str
    :return: None
    """
    message = 'X-DRun-Model-Id:%s' % (normalize_name(model_name))
    print(message, file=sys.__stderr__, flush=True)


def init_metric(model_name):
    """
    Init metrics

    :param model_name: model name
    :type model_name: str
    :return: None
    """
    global _model_name
    _model_name = model_name

    send_model_name(model_name)


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
    _model_name = None
