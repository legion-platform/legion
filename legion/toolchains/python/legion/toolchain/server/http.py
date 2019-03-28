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
Flask package
"""
import functools
import logging
from urllib.parse import parse_qs

import flask

from legion.sdk import config

from legion.sdk.containers import headers
from legion.sdk.utils import normalize_name, parse_value_to_type, EdiHTTPAccessDeniedException

LOGGER = logging.getLogger(__name__)


def _parse_multi_dict(multi_dict, map_func=None):
    """
    Parse MultiDict object and detect lists if they presents (using [] in the end of name)

    :param multi_dict: request data
    :type multi_dict: :py:class:`werkzeug.datastructures.MultiDict`
    :param map_func: function to map all values
    :type map_func: function VAL -> NEW VAL
    :return: dict[str, Any] or dict[str, list[Any]]
    """
    result = {}

    for k in multi_dict:
        if len(k) > 2 and k.endswith('[]'):
            key = k[:-2]
            result[key] = multi_dict.getlist(k)
            if map_func:
                result[key] = [map_func(val) for val in result[key]]
        else:
            result[k] = multi_dict[k]
            if map_func:
                result[k] = map_func(result[k])

    return result


def _parse_url_querystring(querystring_dict):
    """
    Parse URL query strings dictionaries like {'a': ['123'], 'b[]': ['one', 'two']}
    to appropriate dictionaries ({'a': '123', 'b': ['one', 'two']})

    :param querystring_dict: querystring dictionary
    :type querystring_dict: dict
    :return: dict -- parsed and flatted querystring dictionary
    """
    result = {}
    for k in querystring_dict:
        if k.endswith('[]'):
            key = k[:-2]
            result[key] = querystring_dict[k]
        else:
            result[k] = querystring_dict[k][0]
    return result


def parse_batch_request(input_request):
    """
    Parse request in batch mode with payload encoded in body

    :param input_request: request object
    :type input_request: :py:class:`Flask.request`
    :return: list[dict] -- list of dicts with requested fields
    """
    if not input_request.data:
        return []

    return [_parse_url_querystring(parse_qs(line))
            for line in input_request.data.decode('utf-8').split('\n')]


def parse_request(input_request):
    """
    Produce a input dictionary from HTTP request (GET/POST fields, and Files)

    :param input_request: request object
    :type input_request: :py:class:`Flask.request`
    :return: dict with requested fields
    """
    if input_request.method == 'GET':
        return _parse_multi_dict(input_request.args)
    elif input_request.method == 'POST':
        return {
            **_parse_multi_dict(input_request.form),
            **_parse_multi_dict(input_request.files, lambda file: file.read())
        }
    raise ValueError('Unexpected http method: {}'.format(input_request.method))


def prepare_response(response_data, model_id=None, model_version=None, model_endpoint=None):
    """
    Produce an HTTP response from dict/list

    :param response_data: dict/list with data
    :type response_data: dict[str, any] or list[any]
    :param model_id: model id
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :param model_endpoint: model endpoint
    :type model_endpoint: str
    :return: bytes
    """
    response = flask.jsonify(response_data)
    if model_id:
        response.headers[headers.MODEL_ID] = normalize_name(model_id, dns_1035=True)

    if model_version:
        response.headers[headers.MODEL_VERSION] = normalize_name(model_version, dns_1035=True)

    if model_endpoint:
        response.headers[headers.MODEL_ENDPOINT] = normalize_name(model_endpoint, dns_1035=True)

    return response


def _apply_cli_args(application, args):
    """
    Set Flask app instance configuration from arguments

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    args_dict = vars(args)
    for argument, value in args_dict.items():
        if value is not None:
            application.config[argument.upper()] = value


def _copy_configuration(application):
    """
    Set Flask app instance configuration from config (internal file and ENV)

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    for name in config.ALL_VARIABLES:
        value = getattr(config, name)
        if value is not None:
            application.config[name] = value


def configure_application(application, args):
    """
    Initialize configured Flask application instance
    Overall configuration priority: config_default.py, env::FLASK_APP_SETTINGS_FILES file,
    ENV parameters, CLI parameters

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :param args: arguments if provided
    :type args: :py:class:`argparse.Namespace` or None
    :return: None
    """
    # 4th priority: config from file with defaults values
    application.config.from_pyfile('config_default.py')

    # 3rd priority: config from file (path to file from ENV)
    if config.FLASK_APP_SETTINGS_FILES:
        application.config.from_pyfile(config.FLASK_APP_SETTINGS_FILES, True)

    # 2nd priority: config from Legion File, ENV variables
    _copy_configuration(application)

    # 1st priority: config from CLI args
    if args:
        _apply_cli_args(application, args)
