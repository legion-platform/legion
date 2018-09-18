import os
import legion.model

import complex_package.submodule

legion.model.init('complex', '1.0')


legion.model.define_property('prop_1', 0.5)

FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data.dat'))

# write file on train phase
with open(FILE_PATH, 'w') as fstream:
    fstream.write('10')


def on_property_update():
    print('I have got an update!')


legion.model.on_property_update(on_property_update)


def calculate(x):
    # check file availability on execution phase
    assert os.path.exists(FILE_PATH), 'file not exists: {}'.format(FILE_PATH)

    print('I have a property {}'.format(legion.model.properties['prop_1']))

    return complex_package.submodule.add_42(int(x['value']))


legion.model.export_untyped(lambda x: {'result': int(calculate(x))})
legion.model.save('complex.model')
