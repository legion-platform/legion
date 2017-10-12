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
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

from io import BytesIO
from PIL import Image as PYTHON_Image
import base64
import re
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
        :param name: str name of type
        :param native_class: type if class builds on native type
        like int, float and etc. (they should be presented in VALID_NATIVE_TYPES)
        :param description: str of optional type description
        :param default_numpy_type: default numpy type
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
        Get description of type
        :return:
        """
        return self._name if self._name else self.__class__.__name__

    @property
    def description(self):
        """
        Get description of type
        :return:
        """
        return self._description

    @property
    def default_numpy_type(self):
        """
        Get default numpy type
        :return:
        """
        return self._default_numpy_type

    def parse(self, value):
        """
        Parse input value (str, or bytes for files) for base type
        :param value: str or bytes
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
        super(_Bool, self).__init__('Bool', default_numpy_type=np.bool_)

    def parse(self, value):
        """
        Parse boolean strings like 'yes', 'no' and etc. (all listed TRUE_STRINGS in WRONG_STRINGS)
        :param value:
        :return:
        """
        str_value = value.lower()

        if str_value not in self.TRUE_STRINGS + self.WRONG_STRINGS:
            raise ValueError('Invalid value: %s. Valid values is %s and %s' %
                             (value, self.TRUE_STRINGS, self.WRONG_STRINGS))

        return str_value in self.TRUE_STRINGS

    def export(self, value):
        return value


class _Image(BaseType):
    """
    Type for images
    """

    BASE64_REGEX = '^data:image/(.+);base64,(.*)$'

    def __init__(self):
        super(_Image, self).__init__('Image', default_numpy_type=np.object)

    def parse(self, value):
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

    def _load_from_network(self, url):
        data = urlopen(url).read()
        if isinstance(data, str):
            data = data.encode('ascii')
        file = BytesIO(data)
        img = PYTHON_Image.open(file)
        return img

    def _load_from_base64(self, value):
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


class ColumnInformation:
    """
    Column information (type, numpy type)
    """

    def __init__(self, representation_type, numpy_type=None):
        """
        Build column information
        :param representation_type:
        :param numpy_type:
        """
        self._representation_type = representation_type
        self._numpy_type = numpy_type

    @property
    def representation_type(self):
        """
        Get type of column (inherited from BaseType)
        :return: BaseType
        """
        return self._representation_type

    @property
    def numpy_type(self):
        """
        Get numpy type
        :return: numpy.dtype
        """
        if self._numpy_type:
            return self._numpy_type
        else:
            return self.representation_type.default_numpy_type

    @property
    def numpy_type_name(self):
        """
        Get numpy type name
        :return: str name of type
        """
        type_instance = self.numpy_type

        if isinstance(type_instance, type):
            return type_instance.__name__
        else:
            return type_instance.name

    @property
    def description_for_api(self):
        """
        Get information about columns as a dictionary
        :return: dict with type and numpy_type columns
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
    :param extra_columns: optional dict
    :return:
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


def build_df(columns_map, input_values):
    """
    Build pandas.DataFrame from map of columns and input map of strings or bytes
    :param columns_map: dict of str => ColumnInformation
    :param input_values: dict of str => str or bytes
    :return: pandas.DataFrame
    """
    values = {}
    types = {}

    for column_name, column_information in columns_map.items():
        if column_name not in input_values:
            raise Exception('Missed value for column %s' % column_name)

        values[column_name] = column_information.representation_type.parse(input_values[column_name])
        types[column_name] = column_information.numpy_type

    data_frame = pd.DataFrame([values])
    data_frame = data_frame.astype(types)
    return data_frame
