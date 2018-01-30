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
import os
import drun.const.env
import drun.const.headers
from drun.utils import normalize_name, send_header_to_stderr

_model_id = None
_model_initialized_from_function = False


def send_model_id(model_id):
    """
    Send information about model name to stderr

    :param model_id: model name
    :type model_id: str
    :return: None
    """
    send_header_to_stderr(drun.const.headers.MODEL_ID, normalize_name(model_id))


def init(model_id=None):
    """
    Init metrics from value or from ENV

    :param model_id: model name
    :type model_id: str or None
    :return: None
    """
    global _model_id
    global _model_initialized_from_function

    if _model_id:
        raise Exception('Model already has been initialized')

    if model_id:
        _model_initialized_from_function = True
    else:
        _model_initialized_from_function = False
        deducted_model_id = os.getenv(*drun.const.env.MODEL_ID)
        if not deducted_model_id:
            raise Exception('Cannot deduct model name. ENV %s is empty' % drun.const.env.MODEL_ID[0])
        else:
            model_id = deducted_model_id

    model_id = normalize_name(model_id)

    if len(model_id) == 0:
        raise Exception('Model name string length should be greater that 1 (after normalization)')

    _model_id = normalize_name(model_id)
    send_model_id(model_id)


def get_model_id():
    """
    Get current model id

    :return: str or None
    """
    return _model_id


def is_model_id_auto_deduced():
    """
    Is model id has benn auto deduced (from ENV variable)

    :return: bool
    """
    return not _model_initialized_from_function
