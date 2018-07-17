from legion.model.model_id import init
import legion.io

from relative_model.external import plus


init('test summation')


def calculate(x):
    return plus(int(x['a']), int(x['b']))


legion.io.export_untyped(lambda x: {'result': int(calculate(x))},
                         filename='abc.model',
                         version='1.0')
