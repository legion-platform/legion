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
Model HTTP API and utils
"""

import os

import drun.const.env
from PIL import Image as PYTHON_Image


def get_model_base_url(model_name, include_host=True):
    """
    Get model base url from model name

    :param model_name: model name
    :type model_name: str
    :param include_host: include host in path
    :type include_host: bool
    :return: str -- base URL for model calls
    """
    if include_host:
        model_server_url = os.environ.get(*drun.const.env.MODEL_SERVER_URL)
        return '%s/api/model/%s' % (model_server_url, model_name)
    else:
        return '/api/model/%s' % model_name


def get_model_invoke_url(model_name, include_host=True):
    """
    Get model invoke url from model name

    :param model_name: model name
    :type model_name: str
    :param include_host: include host in path
    :type include_host: bool
    :return: str -- invoke URL for model calls
    """
    return get_model_base_url(model_name, include_host) + '/invoke'


def get_requests_parameters_for_model_invoke(**values):
    """
    Query model for calculation

    :param values: values for passing to model. Key should be string (field name), value should be a string
    :type values: dict[str, any]
    :return: dict -- request parameters
    """
    post_fields = {k: v for (k, v) in values.items() if not isinstance(v, bytes)}
    post_files = {k: v for (k, v) in values.items() if isinstance(v, bytes)}
    return {
        'data': post_fields,
        'files': post_files
    }


def load_image(path):
    """
    Load image for model

    :param path: path to local image
    :type path: str
    :return: bytes -- image content
    """
    image = PYTHON_Image.open(path)
    if not isinstance(image, PYTHON_Image.Image):
        raise Exception('Invalid image type')
    return open(path, 'rb').read()
