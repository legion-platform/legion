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
Model types for API calls
"""

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from io import BytesIO
import re

import base64
from PIL import Image as PYTHON_Image
import numpy as np
import pandas as pd

VALID_NATIVE_TYPES = [
    int, float,
    str
]


class BaseType:
    """
    Base model type
    """

    def __init__(self, name=None, native_class=None, description=None, default_numpy_type=np.object):
        """
        Construct base model type

        :param name: name of type
        :type name: str
        :param native_class: type if class builds on native type
        like int, float and etc. (they should be presented in VALID_NATIVE_TYPES)
        :type native_class: int, float and etc or None
        :param description: optional type description
        :type description: str or None
        :param default_numpy_type: default numpy type
        :type :py:class:`numpy.dtype`
        """
        self._name = name
        self._description = description
        self._default_numpy_type = default_numpy_type

        if native_class:
            if native_class not in VALID_NATIVE_TYPES:
                raise Exception('Cannot build type on non-supported native classes')
            self._is_native = True
            self._native_class = native_class
        else:
            self._is_native = False
            self._native_class = native_class

    @property
    def name(self):
        """
        Get name of type

        :return: str
        """
        return self._name if self._name else self.__class__.__name__

    @property
    def description(self):
        """
        Get description of type

        :return: str
        """
        return self._description

    @property
    def default_numpy_type(self):
        """
        Get default numpy type

        :return: :py:class:`numpy.dtype`
        """
        return self._default_numpy_type

    def parse(self, value):
        """
        Parse input value (str, or bytes for files) for base type

        :param value: input value
        :type value: str or bytes
        :return: native representation
        """
        if not self._is_native:
            raise Exception('parse function should be overridden in inherited class')

        return self._native_class(value)

    def export(self, value):
        """
        Export value for base type

        :param value: native representation
        :return: native representation
        """
        if not self._is_native:
            raise Exception('export function should be overridden in inherited class')

        return value

    def __str__(self):
        """
        Get string representation

        :return: str
        """
        return '%s(native_class=%s, description=%s, default_numpy_type=%s)' \
               % (self.name, self._native_class, self._description, self._default_numpy_type)

    def __repr__(self):
        """
        Get string representation

        :return: str
        """
        return '%s(native_class=%r, description=%r, default_numpy_type=%r)' \
               % (self.name, self._native_class, self._description, self._default_numpy_type)


class _Bool(BaseType):
    """
    Type for boolean variables
    """

    TRUE_STRINGS = 'yes', 'true', 't', '1'
    WRONG_STRINGS = 'no', 'false', 'f', '0'

    def __init__(self):
        """
        Construct Bool type
        """
        super(_Bool, self).__init__('Bool', default_numpy_type=np.bool_)

    def parse(self, value):
        """
        Parse boolean strings like 'yes', 'no' and etc. (all listed TRUE_STRINGS in WRONG_STRINGS)

        :param value: input value
        :type value: str or bytes
        :return: bool -- parsed value
        """
        str_value = value.lower()

        if str_value not in self.TRUE_STRINGS + self.WRONG_STRINGS:
            raise ValueError('Invalid value: %s. Valid values is %s and %s' %
                             (value, self.TRUE_STRINGS, self.WRONG_STRINGS))

        return str_value in self.TRUE_STRINGS


class _Image(BaseType):
    """
    Type for images
    """

    BASE64_REGEX = '^data:image/(.+);base64,(.*)$'

    def __init__(self):
        """
        Construct Image type
        """
        super(_Image, self).__init__('Image', default_numpy_type=np.object)

    def parse(self, value):
        """
        Parse image strings or bytes

        :param value: input value
        :type value: str or bytes
        :return: :py:class:`PIL.Image.Image` -- parsed value
        """
        if isinstance(value, str):
            if len(value) > 10 and value[:4] == 'http':
                return self._load_from_network(value)
            elif re.match(self.BASE64_REGEX, value):
                return self._load_from_base64(value)
            else:
                raise Exception('Invalid string: %s' % value)
        elif isinstance(value, bytes):
            file = BytesIO(value)
            return PYTHON_Image.open(file)
        else:
            raise Exception('Invalid data type: %s' % (value.__class__))

    @staticmethod
    def _load_from_network(url):
        """
        Load image from network

        :param url: network image
        :type url: str
        :return: :py:class:`PIL.Image.Image` -- loaded value
        """
        data = urlopen(url).read()
        if isinstance(data, str):
            data = data.encode('ascii')
        file = BytesIO(data)
        img = PYTHON_Image.open(file)
        return img

    def _load_from_base64(self, value):
        """
        Load image from base64

        :param value: base64 string
        :type value: str
        :return: :py:class:`PIL.Image.Image` -- loaded value
        """
        search_results = re.search(self.BASE64_REGEX, value)
        data = search_results.group(2)
        if len(data) % 4:
            data += '=' * (4 - len(data) % 4)
        data = base64.decodebytes(data.encode('ascii'))
        file = BytesIO(data)
        img = PYTHON_Image.open(file)
        return img


Integer = BaseType('Integer', int)
Float = BaseType('Float', float)
String = BaseType('String', str)
Bool = _Bool()
Image = _Image()


# TODO: Rename to LegionType
class ColumnInformation:
    """
    Column information (type, numpy type)
    """

    def __init__(self, representation_type, numpy_type=None):
        """
        Build column information

        :param representation_type: type
        :type representation_type: :py:class:`legion.types.BaseType`
        :param numpy_type: numpy representation type
        :type numpy_type: :py:class:`numpy.dtype` or None
        """
        self._representation_type = representation_type
        self._numpy_type = numpy_type

    @property
    def representation_type(self):
        """
        Get type of column (inherited from BaseType)

        :return: :py:class:`legion.types.BaseType`
        """
        return self._representation_type

    @property
    def numpy_type(self):
        """
        Get numpy type

        :return: :py:class:`numpy.dtype`
        """
        if self._numpy_type:
            return self._numpy_type

        return self.representation_type.default_numpy_type

    @property
    def numpy_type_name(self):
        """
        Get numpy type name

        :return: str -- name of type
        """
        type_instance = self.numpy_type

        if isinstance(type_instance, type):
            return type_instance.__name__

        return type_instance.name

    @property
    def description_for_api(self):
        """
        Get information about columns as a dictionary

        :return: dict[str, any] -- with type and numpy_type columns
        """
        return {
            'type': self.representation_type.name,
            'numpy_type': self.numpy_type_name
        }

    def __repr__(self):
        """
        Get string representation

        :return: str
        """
        return 'ColumnInformation(representation_type=%r, numpy_type=%r)' % (self.representation_type, self.numpy_type)

    def __str__(self):
        """
        Get string representation

        :return: str
        """
        return 'ColumnInformation(representation_type=%s, numpy_type=%s)' % (self.representation_type, self.numpy_type)


# TODO: Add complex
def deduct_types_on_pandas_df(data_frame, extra_columns=None):
    """
    Deduct types on pandas data frame

    :param data_frame: pandas data frame with at least one row
    :type data_frame: :py:class:`pandas.DataFrame`
    :param extra_columns: optional dict
    :type extra_columns: dict[str, :py:class:`legion.types.BaseType`] or None
    :return: dict[str, :py:class:`legion.types.ColumnInformation`]
    """
    types = {}

    for column_name in data_frame.columns:
        column_type = data_frame[column_name].dtype
        sample = data_frame[column_name].iloc[0]

        if isinstance(column_type, np.dtype):
            numpy_name = column_type.name
            if numpy_name[:3] == 'int':
                types[column_name] = ColumnInformation(Integer, column_type)
            elif numpy_name[:4] == 'bool':
                types[column_name] = ColumnInformation(Bool, column_type)
            elif numpy_name[:5] == 'float':
                types[column_name] = ColumnInformation(Float, column_type)
            elif numpy_name[:7] == 'complex':
                types[column_name] = ColumnInformation(Float, column_type)
            elif numpy_name[:6] == 'object':
                if isinstance(sample, str):
                    types[column_name] = ColumnInformation(String, column_type)
                elif isinstance(sample, PYTHON_Image.Image):
                    types[column_name] = ColumnInformation(Image, column_type)
                else:
                    types[column_name] = None
            else:
                types[column_name] = None
        else:
            types[column_name] = None

    if extra_columns:
        for column_name, column_type in extra_columns.items():
            if column_name not in types:
                raise Exception('Undefined column name: %s' % column_name)

            if not isinstance(column_type, BaseType):
                raise Exception('Extra columns dict should contains only instances of classes inherited from BaseType')

            types[column_name] = ColumnInformation(column_type)

    for column_name, column_type in types.items():
        if not column_type:
            raise Exception('Cannot deduct type for column %s' % column_name)

    return types


def build_df(columns_map, input_values, return_dict=False):
    """
    Build pandas.DataFrame (or plain dict) from map of columns and input map of strings or bytes

    :param columns_map: information about columns or None
    :type columns_map: dict[str, :py:class:`legion.types.ColumnInformation`] or None
    :param input_values: input values
    :type input_values: dict[str, union[str, bytes]]
    :param return_dict: return dict instead of pandas DF
    :type return_dict: bool
    :return: :py:class:`pandas.DataFrame` or dict
    """
    values = {}
    types = {}

    if not columns_map:
        return input_values

    for column_name, column_information in columns_map.items():
        if column_name not in input_values:
            raise Exception('Missed value for column %s' % column_name)

        values[column_name] = column_information.representation_type.parse(input_values[column_name])
        types[column_name] = column_information.numpy_type

    if return_dict:
        return values

    data_frame = pd.DataFrame([values])
    data_frame = data_frame.astype(types)
    return data_frame


def get_column_types(param_types):
    """
    Build dict with ColumnInformation from param_types argument for export function

    :param param_types: pandas DF with custom dict or pandas DF.
    Custom dict contains of column_name => legion.BaseType
    :type param_types tuple(:py:class:`pandas.DataFrame`, dict) or :py:class:`pandas.DataFrame`
    :return: dict[str, :py:class:`legion.types.ColumnInformation`] -- column name => column information
    """
    custom_props = None

    if isinstance(param_types, tuple) and len(param_types) == 2 \
            and isinstance(param_types[0], pd.DataFrame) \
            and isinstance(param_types[1], dict):

        pandas_df_sample = param_types[0]
        custom_props = param_types[1]
    elif isinstance(param_types, pd.DataFrame):
        pandas_df_sample = param_types
    else:
        raise Exception('Provided invalid param types: not tuple[DataFrame, dict] or DataFrame')

    return deduct_types_on_pandas_df(data_frame=pandas_df_sample, extra_columns=custom_props)


def deduce_param_types(data_frame, optional_dictionary=None):
    """
    Deduce param types of pandas DF. Optionally overwrite to custom legion.BaseType

    :param data_frame: pandas DF
    :type data_frame: :py:class:`pandas.DataFrame`
    :param optional_dictionary: custom dict contains of column_name => legion.types.BaseType
    :type optional_dictionary: dict[str, :py:class:`legion.types.BaseType`]
    :return: dict[str, :py:class:`legion.types.ColumnInformation`]
    """
    if optional_dictionary:
        return _get_column_types((data_frame, optional_dictionary))

    return _get_column_types(data_frame)


int8 = ColumnInformation(Integer, np.int8)
uint8 = ColumnInformation(Integer, np.uint8)
int16 = ColumnInformation(Integer, np.int16)
uint16 = ColumnInformation(Integer, np.uint16)
int32 = ColumnInformation(Integer, np.int32)
uint32 = ColumnInformation(Integer, np.uint32)
int64 = ColumnInformation(Integer, np.int64)
uint64 = ColumnInformation(Integer, np.uint64)

float16 = ColumnInformation(Float, np.float16)
float32 = ColumnInformation(Float, np.float32)
float64 = ColumnInformation(Float, np.float64)

string = ColumnInformation(String)
boolean = ColumnInformation(Bool)
image = ColumnInformation(Image)
