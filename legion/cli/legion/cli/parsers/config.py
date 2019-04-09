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
Config commands for legion cli
"""
import argparse
import sys

from legion.sdk import utils, config


def _check_variable_exists_or_exit(name):
    """
    Check that variable with desired name exists or print error message and exit with code 1

    :param name: name of variable, case-sensitive
    :type name: str
    :return: None
    """
    if name not in config.ALL_VARIABLES:
        print('Variable {!r} is unknown'.format(name))
        sys.exit(1)


def _print_variable_information(name, show_secrets=False):
    """
    Print information about variable to console

    :param name: name of variable, case-sensitive
    :type name: str
    :param show_secrets: (Optional) do not mask credentials
    :type show_secrets: bool
    :return: None
    """
    description = config.ALL_VARIABLES[name]
    current_value = getattr(config, name)
    is_secret = any(sub in name for sub in ('_PASSWORD', '_TOKEN'))
    print('{} - {}\n  default: {!r}'.format(name, description.description, description.default))
    if current_value != description.default:
        if is_secret and not show_secrets:
            current_value = '****'
        print('  current: {!r}'.format(current_value))


def config_set(args):
    """
    Set configuration variable

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    variable_name = args.key.upper()
    _check_variable_exists_or_exit(variable_name)

    if not config.ALL_VARIABLES[variable_name].configurable_manually:
        raise Exception('Variable {} is not configurable manually'.format(variable_name))

    config.update_config_file(**{variable_name: args.value})

    _print_variable_information(variable_name, True)


def config_get(args):
    """
    Get configuration variable

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    variable_name = args.key.upper()
    _check_variable_exists_or_exit(variable_name)

    _print_variable_information(variable_name, args.show_secrets)


def config_get_all(args):
    """
    Get all configuration variables

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    configurable_values = filter(lambda i: i[1].configurable_manually, config.ALL_VARIABLES.items())
    non_configurable_values = filter(lambda i: not i[1].configurable_manually, config.ALL_VARIABLES.items())

    print('Configurable manually variables:\n===========================')
    for name, _ in configurable_values:
        _print_variable_information(name, args.show_secrets)

    if args.with_system:
        print('\n\n')

        print('System variables:\n===========================')
        for name, _ in non_configurable_values:
            _print_variable_information(name, args.show_secrets)


def config_path(_):
    """
    Get configuration storage path

    :param _: command arguments
    :type _: :py:class:`argparse.Namespace`
    :return: None
    """
    print(config.get_config_file_path())


def list_dependencies(_):
    """
    Print package dependencies

    :param _: command arguments
    :type _: :py:class:`argparse.Namespace`
    :return: None
    """
    dependencies = utils.get_list_of_requirements()
    for name, version in dependencies:
        print('{}=={}'.format(name, version))


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    list_dependencies_parser = main_subparser.add_parser('list-dependencies', description='list package dependencies')
    list_dependencies_parser.set_defaults(func=list_dependencies)

    config_parser = main_subparser.add_parser('config', description='manipulate config')
    config_subparsers = config_parser.add_subparsers()

    config_set_parser = config_subparsers.add_parser('set', description='set configuration variable')
    config_set_parser.add_argument('key', type=str, help='variable name')
    config_set_parser.add_argument('value', type=str, help='variable value')
    config_set_parser.set_defaults(func=config_set)

    config_get_parser = config_subparsers.add_parser('get', description='get configuration variable')
    config_get_parser.add_argument('key', type=str, help='variable name')
    config_get_parser.add_argument('--show-secrets', action='store_true', help='show tokens and passwords')
    config_get_parser.set_defaults(func=config_get)

    config_get_all_parser = config_subparsers.add_parser('get-all', description='get all configuration variables')
    config_get_all_parser.add_argument('--show-secrets', action='store_true', help='show tokens and passwords')
    config_get_all_parser.add_argument('--with-system', action='store_true', help='show with system variables')
    config_get_all_parser.set_defaults(func=config_get_all)

    config_path_parser = config_subparsers.add_parser('path', description='get configuration location')
    config_path_parser.set_defaults(func=config_path)
