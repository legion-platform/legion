import legion.model

import complex_package.submodule

legion.model.init('complex', '1.0')


legion.model.define_property('prop_1', 0.5)


def calculate(x):
    print('I have a property {}'.format(legion.model.properties['prop_1']))

    return complex_package.submodule.add_42(int(x['value']))


legion.model.export_untyped(lambda x: {'result': int(calculate(x))})
legion.model.save('complex.model')
