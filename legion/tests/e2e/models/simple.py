import argparse
import time
import typing

from legion.toolchain import model
from legion.toolchain.model import init, save
from pandas import DataFrame

import store


def default(df: DataFrame) -> typing.Dict[str, int]:
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


def build_model(id: str, version: str) -> None:
    """
    Build mock model for robot tests

    :param id: model id
    :param version: model version
    """
    init(id, version)

    model.export(apply_func=default, column_types={"a": model.string, "b": model.string})
    model.export(apply_func=feedback, column_types={"str": model.string,
                                                    "copies": model.int64}, endpoint='feedback')
    model.export(apply_func=sleep, column_types={"seconds": model.int64}, endpoint='sleep')
    model.export(apply_func=workdir, column_types={"value": model.int64}, endpoint='workdir')

    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='model id', required=True)
    parser.add_argument('--version', help='model version', required=True)
    args = parser.parse_args()

    build_model(args.id, args.version)
