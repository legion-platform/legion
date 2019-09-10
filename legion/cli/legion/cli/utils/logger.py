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
Logger setup
"""
import logging
import sys

from legion.sdk import config


def configure_logging(verbose: bool):
    """
    Set appropriate log level

    :param verbose: logging level
    """
    if verbose or config.DEBUG:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        stream=sys.stderr)
