#!/usr/bin/env python
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
Logging controller
"""

import logging
import os
import sys

import legion.config
import legion.utils

ROOT_LOGGER = logging.getLogger()


def redirect_to_stdout():
    """
    Redirect ROOT log output to stdout
    :return: None
    """
    channel = logging.StreamHandler(sys.stderr)
    channel.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    channel.setFormatter(formatter)
    ROOT_LOGGER.addHandler(channel)


def set_log_level(target=None):
    """
    Update log level to target or to value from ENV
    :param target: target log level (level from logging)
    :type target: str
    :return: None
    """
    if target:
        log_level = target
    else:
        if legion.utils.string_to_bool(os.getenv('VERBOSE', '')):
            log_level = logging.DEBUG
        else:
            log_level = logging.ERROR

    ROOT_LOGGER.setLevel(log_level)
