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

import typing

import click
from legion.sdk.clients.templates import get_legion_template_content
from legion.sdk.clients.templates import get_legion_template_names


@click.group()
def template():
    """
    Allow you to perform actions on legion template files
    """
    pass


@template.command(name='all')
def template_all():
    """
    Get all template names.\n
    Usage example:\n
        legionctl template all\n
    \f
    """
    nl = "\n * "
    click.echo(f'Templates:{nl}{nl.join(get_legion_template_names())}')


@template.command()
@click.option('--name', help='Template name', required=True)
@click.option('--file', '-f', help='Path to the result file', type=click.File('w'))
def generate(name: str, file: typing.TextIO):
    """
    Generate a template by name.\n
    Usage example:\n
        * legionctl template generate --name deployment
    \f
    :param name: Template name
    :param file: Path to the file with only one connection
    """
    file.write(get_legion_template_content(name))

    click.echo(f"{name} template was generated")
