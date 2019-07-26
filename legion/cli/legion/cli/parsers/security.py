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
import logging
import sys

import click
from legion.sdk.clients import edi
from legion.sdk.config import update_config_file

LOG = logging.getLogger(__name__)


@click.command()
@click.option('--edi', 'edi_host', help='EDI server host')
@click.option('--token', help='EDI server jwt token')
def login(edi_host: str, token: str):
    """
    Authorize on EDI endpoint.
    Check that credentials is correct and save to the config
    """
    try:
        edi_clint = edi.RemoteEdiClient(edi_host, token, non_interactive=bool(token))

        edi_clint.info()
        update_config_file(EDI_URL=edi_host, EDI_TOKEN=token)

        print('Success! Credentials have been saved.')
    except edi.IncorrectAuthorizationToken as wrong_token:
        LOG.error('Wrong authorization token\n%s', wrong_token)
        sys.exit(1)


@click.command()
def logout():
    """
    Remove all authorization data from the configuration file
    """
    update_config_file(EDI_URL=None,
                       EDI_TOKEN=None,
                       EDI_REFRESH_TOKEN=None,
                       EDI_ACCESS_TOKEN=None,
                       EDI_ISSUING_URL=None)

    print('All authorization credentials have been removed')
