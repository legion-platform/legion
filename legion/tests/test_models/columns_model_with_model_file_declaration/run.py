import pandas as pd

import legion.model


legion.model.init('columns model', '1.0')


def calculate(x):
    return list(x.keys())


legion.model.export_df(lambda x: {'result': calculate(x)},
                       pd.DataFrame({'c': [3], 'b': [2], 'a': [1]}))
legion.model.save('test-model-binary.bin')
