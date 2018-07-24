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
Model model_id
"""
import legion.containers.headers
import legion.config
from legion.utils import normalize_name, send_header_to_stderr

_model_id = None
_model_version = None


def send_model_information_to_stderr(model_id, model_version):
    """
    Send information about model name to stderr

    :param model_id: model name
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: None
    """
    send_header_to_stderr(legion.containers.headers.MODEL_ID, normalize_name(model_id))
    send_header_to_stderr(legion.containers.headers.MODEL_VERSION, model_version)


def init(model_id, version='1.0'):
    """
    Init metrics from value or from ENV

    :param model_id: model name
    :type model_id: str
    :param version: model version
    :type version: str
    :return: None
    """
    global _model_id
    global _model_version

    if _model_id:
        raise Exception('Model already has been initialized')

    if not model_id:
        raise Exception('Model name string length should be greater that 1 (after normalization)')

    _model_id = normalize_name(model_id)
    _model_version = version
    send_model_information_to_stderr(_model_id, _model_version)


def get_model_id():
    """
    Get current model id

    :return: str or None
    """
    return _model_id


def get_model_version():
    """
    Get current model version

    :return: str or None
    """
    return _model_version
