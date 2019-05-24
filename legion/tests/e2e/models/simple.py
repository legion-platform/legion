import argparse
import random
import time
import typing
from functools import partial

from legion.toolchain import model
from legion.toolchain.model import init, save
from pandas import DataFrame

import store


def default(fail_threshold: int, df: DataFrame) -> typing.Dict[str, int]:
    random_value = random.random()
    if random_value < fail_threshold:
        raise Exception(f'Expected error. Random value is {random_value}. Fail percent is {fail_threshold}')

    return {'result': 42}


def feedback(df: DataFrame) -> typing.Dict[str, str]:
    return {'result': df['str'] * df['copies']}


def sleep(df: DataFrame) -> typing.Dict[str, str]:
    sleep_time = df['seconds']

    time.sleep(sleep_time)

    return {'result': sleep_time}


def _read_resource_from_file() -> int:
    with open('value.txt') as f:
        return int(f.read())


# Check that files and python modules are accessible from current script
print(f'Value from python module: {store.VALUE}')
assert 20 == store.VALUE

print(f'Value from resource file: {_read_resource_from_file()}')
assert 20 == _read_resource_from_file()


def workdir(df: DataFrame) -> typing.Dict[str, str]:
    value: int = df['value']

    return _read_resource_from_file() + store.VALUE + value


def build_model(name: str, version: str) -> None:
    """
    Build mock model for robot tests

    :param name: model name
    :param version: model version
    """
    init(name, version)

    model.export(apply_func=partial(default, args.fail_threshold), column_types={"a": model.string, "b": model.string})
    model.export(apply_func=feedback, column_types={"str": model.string,
                                                    "copies": model.int64}, endpoint='feedback')
    model.export(apply_func=sleep, column_types={"seconds": model.int64}, endpoint='sleep')
    model.export(apply_func=workdir, column_types={"value": model.int64}, endpoint='workdir')

    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='model name', required=True)
    parser.add_argument('--version', help='model version', required=True)
    parser.add_argument('--fail-threshold', type=float, default=0, required=False)
    args = parser.parse_args()

    build_model(args.name, args.version)
