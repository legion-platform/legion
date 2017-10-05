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

VALID_NATIVE_CLASSES = [
    int, float,
    str
]


class BaseType:
    def __init__(self, native_class=None, description=None):
        self._description = description

        if native_class:
            if native_class not in VALID_NATIVE_CLASSES:
                raise Exception('Cannot build type on non-supported native classes')
            self._is_native = True
            self._native_class = native_class
        else:
            self._is_native = False
            self._native_class = native_class

    def parse(self, value):
        if not self._is_native:
            raise Exception('parse function should be overridden in inherited class')

        return self._native_class(value)

    def export(self, value):
        if not self._is_native:
            raise Exception('export function should be overridden in inherited class')

        return value


class _Bool(BaseType):
    TRUE_STRINGS = 'yes', 'true', 't', '1'
    WRONG_STRINGS = 'no', 'false', 'f', '0'

    def parse(self, value):
        str_value = value.lower()

        if str_value not in self.TRUE_STRINGS + self.WRONG_STRINGS:
            raise ValueError('Invalid value: %s. Valid values is %s and %s' %
                             (value, self.TRUE_STRINGS, self.WRONG_STRINGS))

        return str_value in self.TRUE_STRINGS

    def export(self, value):
        return value


class _Image(BaseType):
    BASE64_REGEX = '^data:image/(.+);base64,(.*)$'

    def parse(self, value: str):
        if len(value) > 10 and value[:4] == 'http':
            return self._load_from_network(value)

        if re.match(self.BASE64_REGEX, value):
            return self._load_from_base64(value)

        raise Exception('Invalid data')

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


Integer = BaseType(int)
Float = BaseType(float)
Bool = _Bool()
Image = _Image()
