from legion.model.model_id import init
import legion.io

import complex_package.submodule

init('complex', '1.0')


def calculate(x):
    return complex_package.submodule.add_42(int(x['value']))


legion.io.PyModel().export_untyped(lambda x: {'result': int(calculate(x))}).save('complex.model')
