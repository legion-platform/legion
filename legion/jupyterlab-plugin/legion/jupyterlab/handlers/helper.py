#
#    Copyright 2019 EPAM Systems
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
Declaration of cloud handlers
"""
import functools

from tornado.web import HTTPError

from legion.sdk.clients.edi import EDIConnectionException, IncorrectAuthorizationToken

LEGION_X_JWT_TOKEN = 'X-Jwt'
DEFAULT_EDI_ENDPOINT = 'DEFAULT_EDI_ENDPOINT'
LEGION_OAUTH_TOKEN_COOKIE_NAME = '_legion_oauth_token'
LEGION_OAUTH_STATE_COOKIE_NAME = '_legion_oauth_state'


def decorate_handler_for_exception(function):
    """
    Wrap API handler to properly handle EDI client exceptions

    :param function: function to wrap
    :return: wrapped function
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except IncorrectAuthorizationToken as base_exception:
            raise HTTPError(log_message=str(base_exception), status_code=403) from base_exception
        except EDIConnectionException as base_exception:
            raise HTTPError(log_message=str(base_exception)) from base_exception
    return wrapper


def decorate_async_handler_for_exception(function):
    """
    Wrap async API handler to properly handle EDI client exceptions

    :param function: function to wrap
    :return: wrapped function
    """
    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except IncorrectAuthorizationToken as base_exception:
            raise HTTPError(log_message=str(base_exception), status_code=403) from base_exception
        except EDIConnectionException as base_exception:
            raise HTTPError(log_message=str(base_exception)) from base_exception
    return wrapper


def url_join(*pieces: str) -> str:
    """
    Join url parts, avoid slash duplicates or lacks
    :param pieces: any number of url parts
    :return: url
    """
    return '/'.join(s.strip('/') for s in pieces)
