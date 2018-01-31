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
Exceptions for Drun project
"""


class EdiHTTPException(Exception):
    """
    Exception for EDI server (with HTTP code)
    """

    def __init__(self, http_code, message):
        """
        Build exception

        :param http_code: HTTP code
        :type http_code: int
        :param message: message for user
        :type message: str
        """
        super(EdiHTTPException, self).__init__(message)
        self.http_code = http_code
        self.message = message


class EdiHTTPAccessDeniedException(EdiHTTPException):
    """
    Exception for EDI server -- access denied
    """

    def __init__(self, message='Access denied'):
        """
        Build exception

        :param message: message for user
        :type message: str
        """
        super(EdiHTTPAccessDeniedException, self).__init__(403, message)
