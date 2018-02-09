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

import legion.config
import legion.utils

import flask


def parse_request(input_request):
    """
    Produce a input dictionary from HTTP request (GET/POST fields, and Files)

    :param input_request: request object
    :type input_request: :py:class:`Flask.request`
    :return: dict with requested fields
    """
    result = {}

    # TODO: Add array handl

    # Fill in URL parameters
    for k in input_request.args:
        result[k] = input_request.args[k]

    # Fill in POST parameters
    for k in input_request.form:
        result[k] = input_request.form[k]

    # Fill in Files:
    for k in input_request.files:
        result[k] = input_request.files[k].read()

    return result


def prepare_response(response):
    """
    Produce an HTTP response from dict

    :param response: dict with data
    :type response: dict[str, any]
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
        try:
            response = method(*args, **kwargs)
            code = 200
            if isinstance(response, bool):
                response = {'status': response}
            elif not isinstance(response, dict) and not isinstance(response, list):
                raise Exception('Unknown type returned from api call handler: %s' % type(response))
        except legion.utils.EdiHTTPException as edi_http_exception:
            response = {'error': True, 'message': edi_http_exception.message}
            code = edi_http_exception.http_code
        except Exception as exception:
            response = {'error': True, 'message': str(exception)}
            code = 500

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
                    casted_parameters[field] = fields[field](value)
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

    apply_env_argument(application, legion.config.CONSUL_ADDR[0])
    apply_env_argument(application, legion.config.CONSUL_PORT[0], cast=int)

    apply_env_argument(application, legion.config.LEGION_ADDR[0])
    apply_env_argument(application, legion.config.LEGION_PORT[0], cast=int)
    apply_env_argument(application, legion.config.IP_AUTODISCOVER[0], legion.utils.string_to_bool)

    apply_env_argument(application, legion.config.DEBUG[0], legion.utils.string_to_bool)
    apply_env_argument(application, legion.config.REGISTER_ON_CONSUL[0], legion.utils.string_to_bool)

    apply_env_argument(application, legion.config.DEPLOYMENT[0])
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
