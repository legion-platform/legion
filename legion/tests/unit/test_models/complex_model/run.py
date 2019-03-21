import os

from legion.toolchain import model

import complex_package.submodule
import complex_package.store

model.init('complex', '1.0')


FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data.dat'))

# write file on train phase
with open(FILE_PATH, 'w') as fstream:
    fstream.write('10')


def calculate(x):
    # check file availability on execution phase
    assert os.path.exists(FILE_PATH), 'file not exists: {}'.format(FILE_PATH)

    return complex_package.submodule.add_42(int(x['value']))


def time_callback(x):
    return complex_package.store.time_marker


model.export_untyped(lambda x: {'result': int(calculate(x))})
model.export_untyped(lambda x: {'result': time_callback(x)}, endpoint='time')
model.save()
