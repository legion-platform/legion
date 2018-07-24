import legion.model

import complex_package.submodule

legion.model.init('complex', '1.0')


def calculate(x):
    return complex_package.submodule.add_42(int(x['value']))


legion.model.get_context().export_untyped(lambda x: {'result': int(calculate(x))}).save('complex.model')
