from legion.model.model_id import init
import legion.io


init('test summation', '1.0')


def calculate(x):
    return int(x['a']) + int(x['b'])


legion.io.PyModel().export_untyped(lambda x: {'result': int(calculate(x))}).save('abc.model')
