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
Security commands for legion cli
"""
import argparse
import logging

from legion.sdk.clients import edi
from legion.sdk.config import update_config_file, MODEL_JWT_TOKEN_SECTION

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
    parser.add_argument('--non-interactive',
                        action='store_true',
                        help='Disable interactive mode')
    parser.add_argument('--token',
                        type=str, help='EDI server token (JWT).'
                                       ' If is not provided - oauth2 pipeline will be performed')


def _check_credentials(args):
    """
    Make a request to the server to make sure that credentials are correct

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return bool -- was it successful or not
    """
    # url must be present in args
    # token is optional (for non-interactive login)
    try:
        edi_clint = edi.build_client(args)

        edi_clint.info()
    except edi.IncorrectAuthorizationToken as wrong_token:
        LOG.error('Wrong authorization token\n%s', wrong_token)
        return False

    return True


def _save_temporary_token(edi_url, token):
    """
    Save temporary token to the config file.
    If file or dir doesn't exist then it will be created.
    While we store only security parameters, func can override existed parameters

    :param edi_url: edi url
    :type edi_url: str
    :param token: JWT
    :type token: str
    :return None
    """
    update_config_file(EDI_URL=edi_url, EDI_TOKEN=token)


def login(args):
    """
    Check that credentials is correct and save to the config

    :param args: command arguments
    :type args: argparse.Namespace
    :return: None
    """
    if _check_credentials(args):
        if args.token:
            _save_temporary_token(args.edi, args.token)

            LOG.info('Success! Temporary token has been saved.')
        else:
            LOG.info('You has been authorized before.')


def generate_token(args):
    """
    Generate JWT for specified model

    :param args: command arguments
    :type args: argparse.Namespace
    :return: str -- token
    """
    edi_client = edi.build_client(args)
    token = edi_client.get_token(args.model_role_name, args.expiration_date)

    if token:
        if args.model_deployment_name:
            update_config_file(section=MODEL_JWT_TOKEN_SECTION,
                               **{args.model_deployment_name: token})

        print(token)
    else:
        print('JWT mechanism is disabled')


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    login_parser = main_subparser.add_parser('login', description='Save edi credentials to the config')
    add_edi_arguments(login_parser, required=True)
    login_parser.set_defaults(func=login)

    generate_token_parser = main_subparser.add_parser('generate-token', description='generate JWT token for model')
    generate_token_parser.add_argument('--model-deployment-name', '--md-name', '--md', type=str, help='Model Name',
                                       required=True)
    generate_token_parser.add_argument('--model-role-name', '--md-role', '--role', type=str, help='Model role name')
    generate_token_parser.add_argument('--expiration-date', type=str,
                                       help='Token expiration date in utc: %%Y-%%m-%%dT%%H:%%M:%%S')
    add_edi_arguments(generate_token_parser)
    generate_token_parser.set_defaults(func=generate_token)
