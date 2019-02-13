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

import configparser
import logging
import os
from pathlib import Path

from legion import config
from legion.external import edi

_DEFAULT_CONFIG_PATH = Path.home().joinpath('.legion/config')
LOG = logging.getLogger(__name__)


def add_edi_arguments(parser, required=False):
    """
    Add EDI arguments parser

    :param parser: add arguments to it
    :type parser: argparse.ArgumentParser
    :param required: (Optional) mark edi arguments as required if it equals True
    :type required: bool
    :return: None
    """
    parser.add_argument('--edi',
                        type=str, help='EDI server host', required=required)
    parser.add_argument('--token',
                        type=str, help='EDI server token', required=required)


def _get_config_location():
    """
    Return the config path.
    LEGION_CONFIG can override path value

    :return: Path -- config path
    """
    config_path_from_env = os.getenv(*config.LEGION_CONFIG)

    return Path(config_path_from_env) if config_path_from_env else _DEFAULT_CONFIG_PATH


def _check_credentials(args):
    """
    Make a request to the server to make sure that credentials are correct

    :param args: command arguments with .namespace
    :type args: argparse.Namespace
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
    config_path = _get_config_location()

    config_path.parent.mkdir(mode=0o775, parents=True, exist_ok=True)
    config_path.touch(mode=0o600, exist_ok=True)

    config_parser = configparser.ConfigParser()
    config_parser['security'] = {
        'host': edi_url,
        'token': token
    }

    with config_path.open("w") as config_file:
        config_parser.write(config_file)

    LOG.debug('Save config {} to the file {}'.format(config_parser, config_path))


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


def get_security_params_from_config():
    """
    Return dict with edi url and token from config.
    If an exception occurs during parsing of config or config file doesn't exist then
    return empty dict

    :return: dict[str, str] -- config
    """
    config_path = _get_config_location()

    if config_path.exists():
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(str(config_path))

            return dict(config_parser['security'])
        except Exception as exception:
            LOG.debug('Exception during parsing of legion config {}'.format(exception), exc_info=True)

    return {}


def generate_token(args):
    """
    Generate JWT for specified model
    :param args: command arguments
    :type args: argparse.Namespace
    :return: str -- token
    """
    edi_client = edi.build_client(args)
    token = edi_client.get_token(args.model_id, args.model_version, args.expiration_date)
    print(token)
