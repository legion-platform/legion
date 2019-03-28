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
legion containers exceptions
"""


class IncompatibleLegionModelDockerImage(Exception):
    """
    Exception occurs when user tries to use incompatible docker image (e.g. with missed labels)
    """

    def __init__(self, message):
        """
        Build exception instance

        :param message: description
        :type message: str
        """
        self.message = message
        super().__init__('Incompatible Legion image: {!r}'.format(self.message))
