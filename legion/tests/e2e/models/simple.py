import argparse
import time
import typing

from legion.toolchain import model
from legion.toolchain.model import init, export, save
from pandas import DataFrame


def default(df: DataFrame) -> typing.Dict[str, int]:
    return {'result': 42}


def feedback(df: DataFrame) -> typing.Dict[str, str]:
    return {'result': df['str'] * df['copies']}


def sleep(df: DataFrame) -> typing.Dict[str, str]:
    sleep_time = df['seconds']

    time.sleep(sleep_time)

    return {'result': sleep_time}


def build_model(id: str, version: str) -> None:
    """
    Build mock model for robot tests

    :param id: model id
    :param version: model version
    """
    init(id, version)

<<<<<<< HEAD
<<<<<<< HEAD:tests/models/simple.py
    legion.model.export(apply_func=default, column_types={"a": legion.model.string, "b": legion.model.string})
    legion.model.export(apply_func=feedback, column_types={"str": legion.model.string,
                                                           "copies": legion.model.int64}, endpoint='feedback')
    legion.model.export(apply_func=sleep, column_types={"seconds": legion.model.int64}, endpoint='sleep')
=======
    export(apply_func=default, column_types={"a": model.string, "b": model.string})
    export(apply_func=feedback, column_types={"str": model.string,  "copies": model.int64}, endpoint='feedback')
>>>>>>> [#849] sync files with Refactoring:legion/tests/e2e/models/simple.py
=======
    model.export(apply_func=default, column_types={"a": model.string, "b": model.string})
    model.export(apply_func=feedback, column_types={"str": model.string,
                                                           "copies": model.int64}, endpoint='feedback')
    model.export(apply_func=sleep, column_types={"seconds": model.int64}, endpoint='sleep')
>>>>>>> [#849] sync refactoring

    save('robot.model')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='model id', required=True)
    parser.add_argument('--version', help='model version', required=True)
    args = parser.parse_args()

    build_model(args.id, args.version)
