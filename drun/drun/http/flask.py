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
import os

import drun.const.env
import drun.utils

from flask import jsonify


class HttpProtocolHandler:
    def parse_request(self, input_request):
        """
        Produce a model input dictionary from HTTP request (GET/POST fields, and Files)

        :param input_request: request object
        :type input_request: :py:class:`Flask.request`
        :return: dict with requested fields
        """
        result = {}

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

    def prepare_response(self, response):
        """
        Produce an HTTP response from a model output

        :param response: a model output
        :type response: dict[str, any]
        :return: bytes
        """
        return jsonify(response)


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
    for k, v in args_dict.items():
        if v is not None:
            application.config[k.upper()] = v


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
    apply_env_argument(application, drun.const.env.MODEL_ID[0])
    apply_env_argument(application, drun.const.env.MODEL_FILE[0])

    apply_env_argument(application, drun.const.env.CONSUL_ADDR[0])
    apply_env_argument(application, drun.const.env.CONSUL_PORT[0])

    apply_env_argument(application, drun.const.env.LEGION_ADDR[0])
    apply_env_argument(application, drun.const.env.LEGION_PORT[0])
    apply_env_argument(application, drun.const.env.IP_AUTODISCOVER[0], drun.utils.string_to_bool)

    apply_env_argument(application, drun.const.env.DEBUG[0], drun.utils.string_to_bool)
    apply_env_argument(application, drun.const.env.REGISTER_ON_CONSUL[0], drun.utils.string_to_bool)


def configure_application(application, args):
    """
    Initialize configured Flask application instance
    Overall configuration priority: config_default.py, env::FLASK_APP_SETTINGS_FILES file,
    ENV parameters, CLI parameters

    :param args: arguments if provided
    :type args: :py:class:`argparse.Namespace` or None
    :return: None
    """
    # 4th priority: config from file with defaults values
    application.config.from_pyfile('config_default.py')

    # 3rd priority: config from file (path to file from ENV)
    application.config.from_envvar(drun.const.env.FLASK_APP_SETTINGS_FILES[0], True)

    # 2nd priority: config from ENV variables
    apply_env_args(application)

    # 1st priority: config from CLI args
    if args:
        apply_cli_args(application, args)
