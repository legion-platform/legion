import pandas as pd

from legion.toolchain import model


model.init('columns model', '1.0')


def calculate(x):
    return list(x.keys())


model.export_df(lambda x: {'result': calculate(x)},
                       pd.DataFrame({'c': [3], 'b': [2], 'a': [1]}))
model.save('test-model-binary.bin')
