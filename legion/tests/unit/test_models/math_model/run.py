from legion.toolchain import model

model.init('test math', '1.0')


def algo_sum(x):
    return int(x['a']) + int(x['b'])


def algo_mul(x):
    return int(x['a']) * int(x['b'])


model.export_untyped(lambda x: {'result': int(algo_sum(x))}, endpoint='sum')
model.export_untyped(lambda x: {'result': int(algo_mul(x))}, endpoint='mul')
model.save()
