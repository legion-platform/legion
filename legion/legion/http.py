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
import os
import logging
import urllib

import legion.config
import legion.utils

import flask
from requests.compat import urlencode
from requests.utils import to_key_val_list
from urllib.parse import parse_qs

LOGGER = logging.getLogger(__name__)


def encode_http_params(data):
    """
    Encode HTTP parameters to URL query string

    :param data: data as text or tuple/list
    :type data: str or bytes or tuple or list
    :return: str -- encoded data
    """
    if isinstance(data, (str, bytes)):
        return urlencode(data)
    elif hasattr(data, '__iter__'):
        result = []
        for k, vs in to_key_val_list(data):
            if vs is not None:
                result.append(
                    (k.encode('utf-8') if isinstance(k, str) else k,
                     vs.encode('utf-8') if isinstance(vs, str) else vs))
        return urlencode(result, doseq=True)
    else:
        raise ValueError('Invalid argument')


def parse_multi_dict(multi_dict, map=None):
    """
    Parse MultiDict object and detect lists if they presents (using [] in the end of name)

    :param multi_dict: request data
    :type multi_dict: :py:class:`werkzeug.datastructures.MultiDict`
    :param map: function to map all values
    :type map: function VAL -> NEW VAL
    :return: dict[str, Any] or dict[str, list[Any]]
    """
    result = {}

    for k in multi_dict:
        if len(k) > 2 and k.endswith('[]'):
            key = k[:-2]
            result[key] = multi_dict.getlist(k)
            if map:
                result[key] = [map(val) for val in result[key]]
        else:
            result[k] = multi_dict[k]
            if map:
                result[k] = map(result[k])

    return result


def parse_url_querystring(querystring_dict):
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
        raise Exception('Request does not contain any data')

    return [parse_url_querystring(parse_qs(line))
            for line in input_request.data.decode('utf-8').split('\n')]


def parse_request(input_request):
    """
    Produce a input dictionary from HTTP request (GET/POST fields, and Files)

    :param input_request: request object
    :type input_request: :py:class:`Flask.request`
    :return: dict with requested fields
    """
    result = {}

    # Fill in URL parameters
    result.update(parse_multi_dict(input_request.args))

    # Fill in POST parameters
    result.update(parse_multi_dict(input_request.form))

    # Fill in Files:
    result.update(parse_multi_dict(input_request.files, lambda file: file.read()))

    return result


def prepare_response(response):
    """
    Produce an HTTP response from dict/list

    :param response: dict/list with data
    :type response: dict[str, any] or list[any]
    :return: bytes
    """
    return flask.jsonify(response)


def provide_json_response(method):
    """
    Process response data via JSON formatter

    :param method: decorator function
    :return: decorated function
    """
    @functools.wraps(method)
    def decorated_function(*args, **kwargs):
        code = 200
        try:
            response = method(*args, **kwargs)
            if isinstance(response, bool):
                response = {'status': response}
            elif not isinstance(response, dict) and not isinstance(response, list):
                raise Exception('Wrong value returned from API handler')
        except Exception as exception:
            code = 500
            response = {'error': True,
                        'exception': str(exception)}
            LOGGER.exception('Exception during processing request for {}: {}'
                             .format(method.__name__, exception),
                             exc_info=exception)

        response = prepare_response(response)
        return flask.make_response(response, code)

    return decorated_function


def populate_fields(**fields):
    """
    Populate fields data

    :param fields: fields with formats
    :type fields: dict[str, type]
    :return: decorator function
    """
    def decorator(method):
        @functools.wraps(method)
        def decorated_function(*args, **kwargs):
            parameters = parse_request(flask.request)
            casted_parameters = {}

            for field, value in parameters.items():
                if field not in fields:
                    raise Exception('Unknown parameter: %s' % field)

                try:
                    casted_parameters[field] = legion.utils.parse_value_to_type(value, fields[field])
                except ValueError as cast_value_exception:
                    raise Exception('Cannot cast field %s to %s: %s' % (field, fields[field], cast_value_exception))

            kwargs.update(casted_parameters)

            return method(*args, **kwargs)

        return decorated_function

    return decorator


def authenticate(authenticator):
    """
    Authenticate user

    :param authenticator: callable obj. for checking credentials. Arguments are user and password. Should returns bool.
    :type authenticator: function[user, password]: bool
    :return: decorator function
    """
    def decorator(method):
        @functools.wraps(method)
        def decorated_function(*args, **kwargs):
            auth = flask.request.authorization
            username = None
            password = None

            if auth:
                username = auth.username
                password = auth.password

            if not authenticator(username, password):
                raise legion.utils.EdiHTTPAccessDeniedException()

            return method(*args, **kwargs)

        return decorated_function

    return decorator


def requested_fields(*fields):
    """
    Check that all requested fields has been passed

    :param fields: list of field names
    :type fields: list[str]
    :return: decorator function
    """
    def decorator(method):
        @functools.wraps(method)
        def decorated_function(*args, **kwargs):
            for field in fields:
                if field not in kwargs:
                    raise Exception('Requested field %s s not set' % field)

            return method(*args, **kwargs)

        return decorated_function

    return decorator


def apply_cli_args(application, args):
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


def apply_env_argument(application, name, cast=None):
    """
    Update application config if ENV variable exists

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :param name: environment variable name
    :type name: str
    :param cast: casting of str variable
    :type cast: Callable[[str], Any]
    :return: None
    """
    if name in os.environ:
        value = os.getenv(name)
        if cast:
            value = cast(value)

        application.config[name] = value


def apply_env_args(application):
    """
    Set Flask app instance configuration from environment

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    apply_env_argument(application, legion.config.MODEL_ID[0])
    apply_env_argument(application, legion.config.MODEL_FILE[0])

    apply_env_argument(application, legion.config.LEGION_ADDR[0])
    apply_env_argument(application, legion.config.LEGION_PORT[0], cast=int)

    apply_env_argument(application, legion.config.DEBUG[0], legion.utils.string_to_bool)

    apply_env_argument(application, legion.config.REGISTER_ON_GRAFANA[0], legion.utils.string_to_bool)

    apply_env_argument(application, legion.config.NAMESPACE[0])

    apply_env_argument(application, legion.config.LEGION_API_ADDR[0])
    apply_env_argument(application, legion.config.LEGION_API_PORT[0], cast=int)

    apply_env_argument(application, legion.config.CLUSTER_CONFIG_PATH[0])
    apply_env_argument(application, legion.config.CLUSTER_SECRETS_PATH[0])


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
    application.config.from_envvar(legion.config.FLASK_APP_SETTINGS_FILES[0], True)

    # 2nd priority: config from ENV variables
    apply_env_args(application)

    # 1st priority: config from CLI args
    if args:
        apply_cli_args(application, args)
