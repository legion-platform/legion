from legion.model.model_id import init
import legion.io

import complex_package.submodule

init('complex')


def calculate(x):
    return complex_package.submodule.add_42(int(x['value']))


legion.io.export_untyped(lambda x: {'result': int(calculate(x))},
                         filename='complex.model',
                         version='1.0')
