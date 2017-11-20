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
import sys
import drun.env
from drun.utils import normalize_name

_model_name = None
_model_initialized_from_function = False


def send_model_name(model_name):
    """
    Send information about model name to stderr

    :param model_name: model name
    :type model_name: str
    :return: None
    """
    message = 'X-DRun-Model-Id:%s' % (normalize_name(model_name))
    print(message, file=sys.__stderr__, flush=True)


def init_model(model_name=None):
    """
    Init metrics from value or from ENV

    :param model_name: model name
    :type model_name: str or None
    :return: None
    """
    global _model_name
    global _model_initialized_from_function

    if _model_name:
        raise Exception('Model already has been initialized')

    if model_name:
        _model_initialized_from_function = True
    else:
        _model_initialized_from_function = False
        deducted_model_name = os.getenv(*drun.env.MODEL_ID)
        if not deducted_model_name:
            raise Exception('Cannot deduct model name. ENV %s is empty' % drun.env.MODEL_ID[0])
        else:
            model_name = deducted_model_name

    model_name = normalize_name(model_name)

    if len(model_name) == 0:
        raise Exception('Model name string length should be greater that 1 (after normalization)')

    _model_name = normalize_name(model_name)
    send_model_name(model_name)


def get_model_name():
    """
    Get current model name

    :return: str or None
    """
    return _model_name


def is_model_name_auto_deduced():
    """
    Is model name has benn auto deduced (from ENV variable)

    :return: bool
    """
    return not _model_initialized_from_function
