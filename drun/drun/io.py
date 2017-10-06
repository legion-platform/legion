"""
DRun model export / load
"""

from drun.model import ScipyModel
import drun.types
from drun.types import deduct_types_on_pandas_df

import dill
import os
import zipfile
import tempfile

import drun
from drun.model import ScipyModel, IMLModel
from pandas import DataFrame


def _get_column_types(param_types):
    """
    Build dict with ColumnInformation from param_types argument for export function
    :param param_types: tuple of pandas DF with custom dict or pandas DF.
    Custom dict contains of column_name => drun.BaseType
    :return: dict of column_name => drun.types.ColumnInformation
    """
    pandas_df_sample = None
    custom_props = None

    if isinstance(param_types, tuple) and len(param_types) == 2 \
            and isinstance(param_types[0], DataFrame) \
            and isinstance(param_types[1], dict):

        pandas_df_sample = param_types[0]
        custom_props = param_types[1]
    elif isinstance(param_types, DataFrame):
        pandas_df_sample = param_types
    else:
        raise Exception('Provided invalid param types: not tuple[DataFrame, dict] or DataFrame')

    return deduct_types_on_pandas_df(data_frame=pandas_df_sample, extra_columns=custom_props)


class ModelContainer:
    ZIP_COMPRESSION = zipfile.ZIP_STORED
    ZIP_FILE_MODEL = 'model'
    ZIP_FILE_INFO = 'info.ini'

    def __init__(self, file=None, is_write=False):
        self._file = file
        self._is_saved = not is_write
        self._model = None
        self._properties = {}

        if self._is_saved:
            self._load()

    def _load(self):
        if not os.path.exists(self._file):
            raise Exception('File not existed: %s' % (self._file, ))

        with zipfile.ZipFile(self._file, 'r') as zip:
            with zip.open(self.ZIP_FILE_MODEL, 'rb') as file:
                self._model = dill.load(file)
            with zip.open(self.ZIP_FILE_INFO, 'r') as file:
                self._load_info(file)

    def _load_info(self, file):
        lines = file.read().splitlines()
        lines = [line.split('=', 1) for line in lines if len(line) > 0 and line[0] != '#' and '=' in line]
        self._properties = {k: v for (k, v) in lines}

    def _write_info(self, file):
        for key, value in self._properties.items():
            file.write('%s = %s\n' % (key, value))

    def _add_default_properties(self, model_instance):
        self['model.version'] = model_instance.version
        self['drun.version'] = drun.__version__

    @property
    def model(self):
        if not self._is_saved:
            raise Exception('Cannot get model on non-saved container')

        return self._model

    # TODO: Add temp directory remove
    def save(self, model_instance):
        self._add_default_properties(model_instance)

        temp_directory = tempfile.mkdtemp('drun-model-save')

        with open(os.path.join(temp_directory, self.ZIP_FILE_MODEL), 'wb') as file:
            dill.dump(model_instance, file, recurse=True)
        with open(os.path.join(temp_directory, self.ZIP_FILE_INFO), 'wt') as file:
            self._write_info(file)

        with zipfile.ZipFile(self._file, 'w', self.ZIP_COMPRESSION) as zip:
            zip.write(os.path.join(temp_directory, self.ZIP_FILE_MODEL), self.ZIP_FILE_MODEL)
            zip.write(os.path.join(temp_directory, self.ZIP_FILE_INFO), self.ZIP_FILE_INFO)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __setitem__(self, key, item):
        self._properties[key] = item

    def __getitem__(self, key):
        return self._properties[key]

    def __len__(self):
        return len(self._properties)

    def __delitem__(self, key):
        del self._properties[key]

    def has_key(self, k):
        return k in self._properties

    def update(self, *args, **kwargs):
        return self._properties.update(*args, **kwargs)

    def keys(self):
        return self._properties.keys()

    def values(self):
        return self._properties.values()

    def items(self):
        return self._properties.items()

    def __contains__(self, item):
        return item in self._properties

    def __iter__(self):
        return iter(self._properties)


def export(filename, apply_func, prepare_func=None, param_types=None, version=None):
    """
    Export simple Pandas based model as a bundle
    :param filename: the location to write down the model
    :param apply_func: an apply function DF->DF
    :param prepare_func: a function to prepare input DF->DF
    :param param_types: tuple of pandas DF with custom dict or pandas DF.
    Custom dict contains of column_name => drun.BaseType
    :param version: str of version
    :return: ScipyModel model instance
    """
    if prepare_func is None:
        def prepare_func(input_dict):
            """
            Return input value (default prepare function)
            :param x: dict of values
            :return: dict of values
            """
            return input_dict

    model = ScipyModel(apply_func=apply_func,
                       column_types=_get_column_types(param_types),
                       prepare_func=prepare_func,
                       version=version)

    with ModelContainer(filename, is_write=True) as container:
        container.save(model)

    return model

