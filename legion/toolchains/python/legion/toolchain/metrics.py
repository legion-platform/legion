#
#    Copyright 2019 EPAM Systems
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
import json
import logging
import socket
import sys
import typing
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd
from legion.sdk import config
from legion.sdk.utils import normalize_name

MODEL_UPDATED_AT_TEMPLATE = '%m/%d/%y %H:%M:%S'

STATSD_METRIC_FORMAT = "{}:{}|c"
MODEL_ID_HEADER = "Model ID"
MODEL_VALUE_HEADER = "Model Version"
MODEL_UPDATED_AT_HEADER = "Last Update"
LOGGER = logging.getLogger(__name__)


class Metric(Enum):
    """
    Metric type
    """

    TRAINING_ACCURACY = 'training-accuracy'
    TEST_ACCURACY = 'test-accuracy'
    TRAINING_LOSS = 'training-loss'


def get_metric_endpoint():
    """
    Get metric endpoint

    :return: metric server endpoint
    """
    host = config.METRICS_HOST
    port = config.METRICS_PORT
    namespace = config.NAMESPACE
    return host, port, namespace


def get_build_number():
    """
    Get current build number

    :return: int -- build number
    """
    try:
        return config.BUILD_NUMBER
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


def send_tcp(host: str, port: str, messages: typing.List[str]) -> None:
    """
    Send messages with TCP

    :param host: target host
    :param port: target port
    :param messages: stasd metrics
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    encoded_message = "\n".join(messages).encode('utf-8')
    LOGGER.debug('Send metrics %s to the statsd', encoded_message)

    sock.send(encoded_message)
    sock.close()


def _send_metrics_remotely(model_id: str, metric: str, value: float):
    """
    Send build metric values remotely using statsd format

    :param model_id: model ID
    :param metric: metric type or metric name
    :param value: metric value
    :return: None
    """
    host, port, namespace = get_metric_endpoint()
    messages: typing.List[str] = []

    message = STATSD_METRIC_FORMAT.format(f'{namespace}.{get_metric_name(metric, model_id)}', float(value))
    messages.append(message)

    build_no = get_build_number()
    message = STATSD_METRIC_FORMAT.format(f'{namespace}.{get_metric_name("build", model_id)}', build_no)
    messages.append(message)

    send_tcp(host, port, messages)


def _save_metrics_locally(model_id: str, model_version: str, metric: typing.Union[str, Metric], value: float):
    """
    Save metrics locally to a file

    :param model_id: model ID
    :param model_version: model version
    :param metric: metric type or metric name
    :param value: metric value
    :return: None
    """
    metrics_store_path = Path(config.MODEL_LOCAL_METRIC_STORE)
    metrics_store_path.parent.mkdir(mode=0o775, parents=True, exist_ok=True)
    metrics_store_path.touch(mode=0o775, exist_ok=True)

    if metrics_store_path.stat().st_size == 0:
        build_metrics = {}
    else:
        with open(metrics_store_path, 'r') as f:
            build_metrics = json.load(f)

    if not build_metrics.get(model_id):
        build_metrics[model_id] = {}

    if not build_metrics[model_id].get(model_version):
        build_metrics[model_id][model_version] = {}

    build_metrics[model_id][model_version][metric] = value
    build_metrics[model_id][model_version][MODEL_UPDATED_AT_HEADER] = datetime.now().strftime(MODEL_UPDATED_AT_TEMPLATE)

    with open(metrics_store_path, 'w') as f:
        json.dump(build_metrics, f)


def clear_metric_store(model_id: str, model_version: str):
    """
    Clear metrics from local storage

    :param model_id: model ID
    :param model_version: model version
    :return: None
    """
    metrics_store_path = Path(config.MODEL_LOCAL_METRIC_STORE)
    if not metrics_store_path.exists():
        return

    if metrics_store_path.stat().st_size == 0:
        return

    with open(metrics_store_path, 'r') as f:
        build_metrics = json.load(f)

    if model_id in build_metrics.items():
        if model_version in build_metrics[model_id]:
            del build_metrics[model_id][model_version]

        if not build_metrics[model_id]:
            del build_metrics[model_id]

    with open(metrics_store_path, 'w') as f:
        json.dump(build_metrics, f)


def show_metrics(model_id: str, model_version: typing.Optional[str] = None) -> pd.DataFrame:
    """
    Show metrics from local store

    :param model_id: model ID
    :param model_version: model version
    :return: Metrics which converted to Dataframe
    """
    metrics_store_path = Path(config.MODEL_LOCAL_METRIC_STORE)
    if not metrics_store_path.exists():
        print(f"Can't find local store: {metrics_store_path}", file=sys.stderr)
        return pd.DataFrame()

    with open(metrics_store_path, 'r') as f:
        build_metrics: typing.Dict[str, typing.Dict] = json.load(f)

    metric_keys = set()
    models = []
    for md_id, model_versions in build_metrics.items():
        if model_id != md_id:
            continue

        for version, metrics in model_versions.items():
            if model_version and model_version != version:
                continue

            current_model = {MODEL_ID_HEADER: md_id, MODEL_VALUE_HEADER: version}
            models.append(current_model)

            for metric_name, metric_value in metrics.items():
                if metric_name != MODEL_UPDATED_AT_HEADER:
                    metric_keys.add(metric_name)

                current_model[metric_name] = metric_value

    metric_keys = list(sorted(metric_keys))
    table_header = [MODEL_ID_HEADER, MODEL_VALUE_HEADER, MODEL_UPDATED_AT_HEADER] + metric_keys
    return pd.DataFrame([[model.get(name) for name in table_header] for model in models],
                        columns=table_header)


def send_metric(model_id: str, model_version: str, metric: typing.Union[str, Metric], value: float):
    """
    Send build metric value

    :param model_id: model ID
    :param model_version: model version
    :param metric: metric type or metric name
    :param value: metric value
    :return: None
    """
    metric = metric.value if isinstance(metric, Metric) else str(metric)
    if not config.MODEL_CLUSTER_TRAIN_METRICS_ENABLED:
        _save_metrics_locally(model_id, model_version, metric, value)
    else:
        _send_metrics_remotely(model_id, metric, value)
