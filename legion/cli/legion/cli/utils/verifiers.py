# pylint: disable=W0613
import click


def positive_number(ctx, param: click.core.Option, value):
    """
    Check that CLI parameters is positive number

    :param ctx: click context
    :param param: param name
    :param value: pa-ram value
    :return: cli value
    """
    if int(value) <= 0:
        raise click.BadParameter(f'{param.name} must be positive integer')

    return value
