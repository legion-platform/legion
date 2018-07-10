from legion.model.model_id import init
import legion.io


init('io model')

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


legion.io.export_untyped(lambda x: {'result': int(calculate(x))},
                         filename='io.model',
                         version='1.0')
