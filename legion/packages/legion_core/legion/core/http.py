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
HTTP utils
"""
import logging

from requests.compat import urlencode
from requests.utils import to_key_val_list


LOGGER = logging.getLogger(__name__)


def encode_http_params(data):
    """
    Encode HTTP parameters to URL query string

    :param data: data as text or tuple/list
    :type data: str or bytes or tuple or list
    :return: str -- encoded data
    """
    if isinstance(data, (str, bytes)):
        return urlencode(data)
    elif hasattr(data, '__iter__'):
        result = []
        for key, value in to_key_val_list(data):
            if value is not None:
                result.append(
                    (key.encode('utf-8') if isinstance(key, str) else key,
                     value.encode('utf-8') if isinstance(value, str) else value))
        return urlencode(result, doseq=True)
    raise ValueError('Invalid argument')



