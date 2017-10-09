"""
DRun model export / load
"""

from drun.model import ScipyModel
import drun.types
from drun.types import deduct_types_on_pandas_df
from drun.types import ColumnInformation

import dill
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


def deduce_param_types(data_frame, optional_dictionary=None):
    """
    Deduce param types of pandas DF. Optionally overwrite to custom drun.BaseType
    :param data_frame: pandas DF
    :param optional_dictionary: custom dict contains of column_name => drun.BaseType
    :return: dict of column_name => drun.types.ColumnInformation
    """
    if optional_dictionary:
        return _get_column_types((data_frame, optional_dictionary))
    else:
        return _get_column_types(data_frame)


def export(filename, apply_func, prepare_func=None, param_types=None, input_data_frame=None, version=None):
    """
    Export simple Pandas based model as a bundle
    :param filename: the location to write down the model
    :param apply_func: an apply function DF->DF
    :param prepare_func: a function to prepare input DF->DF
    :param param_types: result of deduce_param_types
    :param input_data_frame: pandas DF
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

    with open(filename, 'wb') as file:
        dill.dump(model, file, recurse=True)

    return model


def load_model(filename):
    """
    Load a model bundle from the given file
    :param filename: A name of the model bundle
    :return: an implementation of drun.model.IMLModel
    """
    with open(filename, 'rb') as file:
        model = dill.load(file)
        return model
