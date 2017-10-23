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
import typing
from enum import Enum

import drun.env


class Metric(Enum):
    """
    Metric type
    """

    TRAINING_ACCURACY = 'training_accuracy'
    TEST_ACCURACY = 'test_accuracy'
    TRAINING_LOSS = 'training_loss'


def get_metric_endpoint() -> typing.Tuple[str, int]:
    """
    Get metric endpoint

    :return: metric server endpoint
    """
    host = os.getenv(*drun.env.METRIC_ENDPOINT_HOST)
    port = int(os.getenv(*drun.env.METRIC_ENDPOINT_PORT))
    return host, port


def get_metric_label() -> str:
    """
    Get actual metrics label

    :return: str -- metrics label (axis X)
    """
    metric_label = os.getenv(*drun.env.METRIC_LABEL)
    build_number = os.getenv(*drun.env.BUILD_NUMBER)

    if metric_label:
        return metric_label

    if build_number:
        return build_number

    raise Exception('Cannot get metrics label: %s and %s are empty'
                    % (drun.env.METRIC_LABEL[0], drun.env.BUILD_NUMBER[0]))


def send_metric_float(metric: Metric, value: float) -> None:
    """
    Send metric value (float)

    :param metric: metric type
    :type metric: :py:class:`drun.metrics.Metric`
    :param value: metric value
    :type value: float
    :return: None
    """
    pass

