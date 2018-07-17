from legion.model.model_id import init
import legion.io

import legion.model

import legion.pymodel

legion.model.init('test summation', '1.0', type='pymodel')  # same as below

legion.model.define_property('prop_1', default=0.5, type=legion.model.float32)  # by default float32, default value is 0.0


py_model = legion.pymodel.Model('test summation', '1.0')  # do the same shit as model.init does
                                                          # and set legion.model.context

py_model.define_property('prop_1', default=0.5, type=legion.model.float32)  # by default float32, default value is 0.0
py_model.on_property_change(lambda key: print(key))

py_model.send_metrics('metric_a', 1.0)


def calculate(x):
    a = legion.model.properties['prop_1']
    return int(x['a']) + int(x['b'])

calculate({'a': 1.0})

py_model.export_untyped(lambda x: {'result': int(calculate(x))})
py_model.save('abc.model')
