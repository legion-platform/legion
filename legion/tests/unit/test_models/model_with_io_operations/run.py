from legion.toolchain import model


model.init('io model', '1.0')

FILE = 'dataset.txt'


def write_dataset():
    with open(FILE, 'w') as train_dataset:
        train_dataset.write('42')


def read_dataset():
    with open(FILE, 'r') as ready_dataset:
        return int(ready_dataset.read())


write_dataset()


def calculate(x):
    value = read_dataset()
    return int(x['value']) + value


model.export_untyped(lambda x: {'result': int(calculate(x))})
model.save()
