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
Output util functions
"""

import json
import typing
from collections import OrderedDict

import click
import yaml
from jsonpath_rw import parse
from texttable import Texttable

from legion.sdk.models.base_model_ import Model

SPLIT_SIGN = "="

MAX_TABLE_WIDTH = 200
MAX_TABLE_VALUE_LENGTH = 50

JSON_OUTPUT_FORMAT = "json"
YAML_OUTPUT_FORMAT = "yaml"
TABLE_OUTPUT_FORMAT = "table"
JSONPATH_OUTPUT_FORMAT = "jsonpath"
DEFAULT_OUTPUT_FORMAT = YAML_OUTPUT_FORMAT

ALL_OUTPUT_FORMATS = [
    JSON_OUTPUT_FORMAT,
    TABLE_OUTPUT_FORMAT,
    YAML_OUTPUT_FORMAT,
    JSONPATH_OUTPUT_FORMAT
]


# pylint: disable=W0613
def validate_output_format(ctx, param, value):
    """
    Custom validator for "--output-format" parameter.
    It's an analog of click.Choise

    :param ctx: click context
    :param param: param name
    :param value: param value
    :return: cli value
    """
    splited_output_format = value.split(SPLIT_SIGN, maxsplit=1)
    if splited_output_format[0] not in ALL_OUTPUT_FORMATS:
        raise click.BadParameter(f'invalid choice: {value}. (choose from {", ".join(ALL_OUTPUT_FORMATS)})')

    return value


def flatten_dict(d: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """
    Flat keys of a dictionary.
    For example: {"a": {"b": 1}, "c": 2} produces {"a.b": 1, "c": 2}
    :param d: input dictionary
    :return: flatten dictionary
    """

    def expand(key, value):
        if isinstance(value, dict):
            return [(key + '.' + k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return OrderedDict(items)


def _restrict_table_value_length(value: str) -> str:
    """
    Reduce the length of a table cell
    :param value: table cell
    :return: reduced cell of a table
    """
    if len(value) < MAX_TABLE_VALUE_LENGTH:
        return value
    else:
        return str(value)[:MAX_TABLE_VALUE_LENGTH] + "..."


def _convert_model_values(model: Model) -> typing.List[str]:
    """
    Convert a legion entity to a flatten dict
    :param model: legion entity
    :return: flatten dict
    """
    return list(
        map(
            lambda x: _restrict_table_value_length(str(x)),
            flatten_dict(model.to_dict()).values()
        )
    )


def show_table(models: typing.List[Model]):
    """
    Produce table to stdout from list of legion models
    :param models: legion models
    """
    if not models:
        click.echo("Empty!")
        return

    headers = list(flatten_dict(models[0].to_dict()).keys())
    table = Texttable(MAX_TABLE_WIDTH)

    table.add_rows([headers] + [_convert_model_values(md) for md in models])
    click.echo(table.draw() + "\n")


def extract_jsonpath(models: typing.List[Model], expr: str):
    """
    Apply jsonpath expression to the list of modules
    :param models: legion models
    :param expr: jsonpath expression
    """
    jsonpath_expr = parse(expr)

    result = [match.value for match in jsonpath_expr.find([md.to_dict() for md in models])]

    click.echo(result[0] if len(result) == 1 else json.dumps(result))


def format_output(models: typing.List[Model], output_format: str):
    """
    Write legion models to stdout by specific output format
    :param models: legion models
    :param output_format: output format
    """
    splitted_output_format = output_format.split(SPLIT_SIGN, maxsplit=1)
    output_format, expression = splitted_output_format[0], ""
    if len(splitted_output_format) == 2:
        expression = splitted_output_format[1]

    if output_format == JSON_OUTPUT_FORMAT:
        click.echo(json.dumps([m.to_dict() for m in models]))
    elif output_format == YAML_OUTPUT_FORMAT:
        click.echo(yaml.dump([m.to_dict() for m in models]))
    elif output_format == TABLE_OUTPUT_FORMAT:
        show_table(models)
    elif output_format == JSONPATH_OUTPUT_FORMAT:
        extract_jsonpath(models, expression)
    else:
        raise ValueError(f'Not expected {output_format} output format')
