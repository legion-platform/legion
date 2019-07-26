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
import sys

import click
from legion.sdk import config


@click.group(name='config')
def config_group():
    """
    Legion CLI config manipulation
    """
    pass


@config_group.command(name="set")
@click.argument('key', type=str, required=True)
@click.argument('value', type=str, required=True)
def config_set(key: str, value: str):
    """
    Set configuration variable.\n
    Usage example:\n
        * legionctl config set EDI_URL http://localhost:5000
    \f
    :param key: Configuration variable name
    :param value: Configuration variable name
    """
    variable_name = key.upper()
    _check_variable_exists_or_exit(variable_name)

    if not config.ALL_VARIABLES[variable_name].configurable_manually:
        raise Exception('Variable {} is not configurable manually'.format(variable_name))

    config.update_config_file(**{variable_name: value})

    _print_variable_information(variable_name, True)


@config_group.command(name="get")
@click.argument('key', type=str, required=True)
@click.option('--show-secrets/--no-show-secrets', default=False, help='Show tokens and passwords')
def config_get(key: str, show_secrets: bool):
    """
    Get configuration variable value\n
    Usage example:\n
        * legionctl config get EDI_URL --show-secrets
    \f
    :param key: Configuration variable name
    :param show_secrets: Show tokens and passwords
    """
    variable_name = key.upper()
    _check_variable_exists_or_exit(variable_name)

    _print_variable_information(variable_name, show_secrets)


@config_group.command(name="all")
@click.option('--show-secrets/--no-show-secrets', default=False, help='Show tokens and passwords')
@click.option('--with-system/--no-with-system', default=False, help='Show with system variables')
def config_get_all(show_secrets: bool, with_system: bool):
    """
    Get all configuration variables\n
    Usage example:\n
        * legionctl config all --show-secrets --with-system
    \f
    :param with_system: Show with system variables
    :param show_secrets: Show tokens and passwords
    """
    configurable_values = filter(lambda i: i[1].configurable_manually, config.ALL_VARIABLES.items())
    non_configurable_values = filter(lambda i: not i[1].configurable_manually, config.ALL_VARIABLES.items())

    click.echo('Configurable manually variables:\n===========================')
    for name, _ in configurable_values:
        _print_variable_information(name, show_secrets)

    if with_system:
        click.echo('\n\n')

        click.echo('System variables:\n===========================')
        for name, _ in non_configurable_values:
            _print_variable_information(name, show_secrets)


@config_group.command(name="path")
def config_path():
    """
    Get configuration storage
    Usage example:\n
        * legionctl config path
    \f
    """
    click.echo(config.get_config_file_path())


def _check_variable_exists_or_exit(name: str):
    """
    Check that variable with desired name exists or print error message and exit with code 1

    :param name: name of variable, case-sensitive
    """
    if name not in config.ALL_VARIABLES:
        click.echo('Variable {!r} is unknown'.format(name))
        sys.exit(1)


def _print_variable_information(name: str, show_secrets: bool = False):
    """
    Print information about variable to console

    :param name: name of variable, case-sensitive
    :param show_secrets: do not mask credentials
    :return: None
    """
    description = config.ALL_VARIABLES[name]
    current_value = getattr(config, name)
    is_secret = any(sub in name for sub in ('_PASSWORD', '_TOKEN'))
    click.echo('{} - {}\n  default: {!r}'.format(name, description.description, description.default))
    if current_value != description.default:
        if is_secret and not show_secrets:
            current_value = '****'
        click.echo('  current: {!r}'.format(current_value))
