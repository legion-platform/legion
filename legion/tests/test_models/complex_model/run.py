import os
import time

import legion.model

import complex_package.submodule
import complex_package.store

legion.model.init('complex', '1.0')

legion.model.define_property('prop_1', 0.5)

FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data.dat'))


# write file on train phase
with open(FILE_PATH, 'w') as fstream:
    fstream.write('10')


def on_property_change():
    print('I have got an update!')
    time.sleep(1)
    print('I am ready for update')
    complex_package.store.time_marker = int(time.time())


legion.model.on_property_change(on_property_change)


def calculate(x):
    # check file availability on execution phase
    assert os.path.exists(FILE_PATH), 'file not exists: {}'.format(FILE_PATH)

    print('I have a property {}'.format(legion.model.properties['prop_1']))

    return complex_package.submodule.add_42(int(x['value']))


def time_callback(x):
    return complex_package.store.time_marker


legion.model.export_untyped(lambda x: {'result': int(calculate(x))})
legion.model.export_untyped(lambda x: {'result': time_callback(x)}, endpoint='time')
legion.model.save('complex.model')
