#
#    Copyright 2018 EPAM Systems
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
Security logic for legion
"""
import logging

import legion.config
from legion.external import edi

LOG = logging.getLogger(__name__)
SECURITY_SECTION_NAME = 'security'


def add_edi_arguments(parser, required=False):
    """
    Add EDI arguments parser

    :param parser: add arguments to it
    :type parser: :py:class:`argparse.ArgumentParser`
    :param required: (Optional) mark edi arguments as required if it equals True
    :type required: bool
    :return: None
    """
    parser.add_argument('--edi',
                        type=str, help='EDI server host', required=required)
    parser.add_argument('--token',
                        type=str, help='EDI server token', required=required)


def _check_credentials(args):
    """
    Make a request to the server to make sure that credentials are correct

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return None
    """
    # url and token must presents in args
    edi_clint = edi.build_client(args)

    edi_clint.info()


def _save_credentials(edi_url, token):
    """
    Save credentials to the config file.
    If file or dir doesn't exist then it will be created.
    While we store only security parameters, func can override existed parameters

    :param edi_url: edi url
    :type edi_url: str
    :param token: dex token
    :type token: str
    :return None
    """
    legion.config.update_config_file(EDI_URL=edi_url,
                                     EDI_TOKEN=token)


def login(args):
    """
    Check that credentials is correct and save to the config

    :param args: command arguments
    :type args: argparse.Namespace
    :return: None
    """
    _check_credentials(args)
    _save_credentials(args.edi, args.token)

    LOG.info('Success! Credentials were saved.')
