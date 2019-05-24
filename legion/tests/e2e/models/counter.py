import argparse
import random
import typing
from functools import partial

from legion.toolchain import model
from legion.toolchain.model import init, save
from pandas import DataFrame

COUNTER = 0


def default(fail_threshold: int, df: DataFrame) -> typing.Dict[str, int]:
    random_value = random.random()
    if random_value < fail_threshold:
        raise Exception(f'Expected error. Random value is {random_value}. Fail percent is {fail_threshold}')

    global COUNTER
    COUNTER += 1

    return {'result': COUNTER}


def build_model(name: str, version: str) -> None:
    """
    Build mock model for robot tests

    :param name: model name
    :param version: model version
    """
    init(name, version)

    model.export(apply_func=partial(default, args.fail_threshold), column_types={"a": model.string, "b": model.string})

    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='model name', required=True)
    parser.add_argument('--version', help='model version', required=True)
    parser.add_argument('--fail-threshold', type=float, default=0, required=False)
    args = parser.parse_args()

    build_model(args.name, args.version)
