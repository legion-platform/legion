#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
"""
DRun model export / load
"""

import os
import zipfile
import json

import drun
from drun.model import ScipyModel, IMLModel
import drun.types
from drun.types import deduct_types_on_pandas_df
from drun.types import ColumnInformation
from drun.utils import TemporaryFolder

import dill
from pandas import DataFrame


def _get_column_types(param_types):
    """
    Build dict with ColumnInformation from param_types argument for export function

    :param param_types: pandas DF with custom dict or pandas DF.
    Custom dict contains of column_name => drun.BaseType
    :type param_types tuple(:py:class:`pandas.DataFrame`, dict) or :py:class:`pandas.DataFrame`
    :return: dict[str, :py:class:`drun.types.ColumnInformation`] -- column name => column information
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
    """
    Archive representation of model with meta information (properties, str => str)
    """

    ZIP_COMPRESSION = zipfile.ZIP_STORED
    ZIP_FILE_MODEL = 'model'
    ZIP_FILE_INFO = 'info.json'

    def __init__(self, file, is_write=False, do_not_load_model=False):
        """
        Create model container (archive) from existing (when is_write=False) or from empty (when is_write=True)

        :param file: path to file for load or save in future
        :type file: str
        :param is_write: flag for create empty container (not read)
        :type is_write: bool
        :param do_not_load_model: load only meta information
        :type do_not_load_model: bool
        """
        self._file = file
        self._is_saved = not is_write
        self._do_not_load_model = do_not_load_model
        self._model = None
        self._properties = {}

        if self._is_saved:
            self._load()

    def _load(self):
        """
        Load from file

        :return: None
        """
        if not os.path.exists(self._file):
            raise Exception('File not existed: %s' % (self._file, ))

        with TemporaryFolder('drun-model-save') as temp_directory:
            with zipfile.ZipFile(self._file, 'r') as zip:
                model_path = zip.extract(self.ZIP_FILE_MODEL, os.path.join(temp_directory.path, self.ZIP_FILE_MODEL))
                info_path = zip.extract(self.ZIP_FILE_INFO, os.path.join(temp_directory.path, self.ZIP_FILE_INFO))

            if not self._do_not_load_model:
                with open(model_path, 'rb') as file:
                    self._model = dill.load(file)

            with open(info_path, 'r') as file:
                self._load_info(file)

    def _load_info(self, file):
        """
        Read properties from file-like object (using .read)

        :param file: source file
        :type file: file-like object
        :return: None
        """
        self._properties = json.load(file)

    def _write_info(self, file):
        """
        Write properties to file-like object (using .write)

        :param file: target file
        :type file: file-like object
        :return: None
        """
        json.dump(self._properties, file)

    def _add_default_properties(self):
        """
        Add default properties during saving of model

        :return: None
        """
        self['model.version'] = self._model.version
        self['drun.version'] = drun.__version__
        self['jenkins.build_number'] = os.environ.get('BUILD_NUMBER')
        self['jenkins.commit'] = os.environ.get('BUILD_COMMIT')
        self['jenkins.node_name'] = os.environ.get('NODE_NAME')

    @property
    def model(self):
        """
        Get instance of model if it has been loaded or saved

        :return: :py:class:`drun.model.IMLModel` -- instance of model
        """
        if not self._is_saved:
            raise Exception('Cannot get model on non-saved container')

        return self._model

    def save(self, model_instance):
        """
        Save to file

        :param model_instance: model
        :type model_instance: :py:class:`drun.model.IMLModel`
        :return: None
        """
        self._model = model_instance
        self._add_default_properties()

        with TemporaryFolder('drun-model-save') as temp_directory:
            with open(os.path.join(temp_directory.path, self.ZIP_FILE_MODEL), 'wb') as file:
                dill.dump(model_instance, file, recurse=True)
            with open(os.path.join(temp_directory.path, self.ZIP_FILE_INFO), 'wt') as file:
                self._write_info(file)

            with zipfile.ZipFile(self._file, 'w', self.ZIP_COMPRESSION) as zip:
                zip.write(os.path.join(temp_directory.path, self.ZIP_FILE_MODEL), self.ZIP_FILE_MODEL)
                zip.write(os.path.join(temp_directory.path, self.ZIP_FILE_INFO), self.ZIP_FILE_INFO)

    def __enter__(self):
        """
        Return self on context enter

        :return: :py:class:`drun.io.ModelContainer`
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Call remove on context exit

        :param type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        pass

    def __setitem__(self, key, item):
        """
        Set property value (without save)

        :param key: key
        :type key: str
        :param item: value
        :type key: str
        :return: None
        """
        self._properties[key] = item

    def __getitem__(self, key):
        """
        Get property value

        :param key: key
        :type key: str
        :return: str -- value
        """
        return self._properties[key]

    def __len__(self):
        """
        Get count of properties

        :return: int -- count of properties
        """
        return len(self._properties)

    def __delitem__(self, key):
        """
        Remove property by key

        :param key: key
        :type key: str
        :return: None
        """
        del self._properties[key]

    def has_key(self, k):
        """
        Check that property with specific key exists

        :param k: key
        :type k: str
        :return: bool -- check result
        """
        return k in self._properties

    def update(self, *args, **kwargs):
        """
        Update property dict with another values

        :param args: args
        :type args: tuple
        :param kwargs: kwargs
        :type args: dict
        :return: any result of update
        """
        return self._properties.update(*args, **kwargs)

    def keys(self):
        """
        Get tuple of properties keys

        :return: tuple of properties keys
        """
        return tuple(self._properties.keys())

    def values(self):
        """
        Get tuple of properties values

        :return: tuple of properties values
        """
        return tuple(self._properties.values())

    def items(self):
        """
        Get tuple of properties (key, value)

        :return: tuple of (key, value)
        """
        return self._properties.items()

    def get(self, key, default=None):
        """
        Get property value or default value

        :param key: key
        :type key: str
        :param default: any default value
        :type default: any
        :return: str or value of default
        """
        if key in self._properties:
            return self[key]
        return default

    def __contains__(self, k):
        """
        Check that property with specific key exists

        :param k: key
        :type k: str
        :return: bool check result
        """
        return k in self._properties

    def __iter__(self):
        """
        Iterate over properties

        :return: iterator
        """
        return iter(self._properties)


def deduce_param_types(data_frame, optional_dictionary=None):
    """
    Deduce param types of pandas DF. Optionally overwrite to custom drun.BaseType

    :param data_frame: pandas DF
    :type data_frame: :py:class:`pandas.DataFrame`
    :param optional_dictionary: custom dict contains of column_name => drun.types.BaseType
    :type optional_dictionary: dict[str, :py:class:`drun.types.BaseType`]
    :return: dict[str, :py:class:`drun.types.ColumnInformation`]
    """
    if optional_dictionary:
        return _get_column_types((data_frame, optional_dictionary))
    else:
        return _get_column_types(data_frame)


def export(filename, apply_func, prepare_func=None, param_types=None, input_data_frame=None, version=None):
    """
    Export simple Pandas based model as a bundle

    :param filename: the location to write down the model
    :type filename: str
    :param apply_func: an apply function DF->DF
    :type apply_func: func(x) -> y
    :param prepare_func: a function to prepare input DF->DF
    :type prepare_func: func(x) -> y
    :param param_types: result of deduce_param_types
    :type param_types: dict[str, :py:class:`drun.types.ColumnInformation`]
    :param input_data_frame: pandas DF
    :type input_data_frame: :py:class:`pandas.DataFrame`
    :param version: of version
    :type version: str
    :return: :py:class:`drun.model.ScipyModel` -- model instance
    """
    if prepare_func is None:
        def prepare_func(input_dict):
            """
            Return input value (default prepare function)
            :param x: dict of values
            :return: dict of values
            """
            return input_dict

    column_types = None

    if param_types is not None and input_data_frame is not None:
        raise Exception('You cannot provide param_types and input_data_frame in one time')

    if param_types is None and input_data_frame is None:
        raise Exception('You should provide param_types or input_data_frame')

    if param_types is not None:
        column_types = param_types
    elif input_data_frame is not None:
        column_types = _get_column_types(input_data_frame)

    if not isinstance(column_types, dict) \
            or not len(column_types.keys()) \
            or not isinstance(list(column_types.values())[0], ColumnInformation):
        raise Exception('Bad param_types / input_data_frame provided')

    model = ScipyModel(apply_func=apply_func,
                       column_types=column_types,
                       prepare_func=prepare_func,
                       version=version)

    with ModelContainer(filename, is_write=True) as container:
        container.save(model)

    return model
