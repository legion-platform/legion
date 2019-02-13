#
#   Copyright 2018 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
Module fore remote debugging python code in docker containers
PYDEVD_HOST and PYDEVD_PORT should be set to valid values
"""
import os
import sys
import logging

LOGGER = logging.getLogger(__name__)

try:
    PYDEVD_HOST = os.getenv('PYDEVD_HOST')
    PYDEVD_PORT = os.getenv('PYDEVD_PORT')

    if PYDEVD_HOST and PYDEVD_PORT:
        import pydevd  # pylint: disable=F0401

        try:
            PYDEVD_PORT = int(PYDEVD_PORT)
        except ValueError as value_error:
            PYDEVD_PORT = None
            LOGGER.exception('Invalid port value: {}'.format(PYDEVD_PORT), exc_info=value_error)

        if PYDEVD_PORT:
            print('pydevd is connecting to {}:{}'.format(PYDEVD_HOST, PYDEVD_PORT), file=sys.__stdout__)
            pydevd.settrace(
                host=PYDEVD_HOST,
                port=PYDEVD_PORT,
                suspend=False,
                patch_multiprocessing=True,
                stdoutToServer=True,
                stderrToServer=True)
except ModuleNotFoundError:
    LOGGER.exception('Cannot import module pydevd')
except ImportError as import_error:
    LOGGER.exception('Unable to import pydevd package', exc_info=import_error)
except Exception as pydevd_connection_exception:
    LOGGER.exception('Unable to connect to pydevd. Ignoring...',
                     exc_info=pydevd_connection_exception)

try:
    PTVSD_HOST = os.getenv('PTVSD_HOST', '0.0.0.0')
    PTVSD_PORT = os.getenv('PTVSD_PORT')
    PTVSD_WAIT_ATTACH = os.getenv('PTVSD_WAIT_ATTACH', '0')

    if PTVSD_PORT:
        import ptvsd

        ptvsd.enable_attach(address=(PTVSD_HOST, PTVSD_PORT))
        print('ptvsd has been enabled on {}:{}'.format(PTVSD_HOST, PTVSD_PORT), file=sys.__stdout__)
        if PTVSD_WAIT_ATTACH == '1':
            print('ptvsd is waiting for attach', file=sys.__stdout__)
            ptvsd.wait_for_attach()
except ModuleNotFoundError:
    LOGGER.exception('Cannot import module ptvsd')
except ImportError as import_error:
    LOGGER.exception('Unable to import ptvsd package', exc_info=import_error)
except Exception as pydevd_connection_exception:
    LOGGER.exception('Unable to start ptvsd',
                     exc_info=pydevd_connection_exception)
