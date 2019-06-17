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
EDI client
"""
import argparse
import logging
import typing

from legion.sdk import config
from legion.sdk.clients.edi import RemoteEdiClient
from legion.sdk.definitions import VCS_URL

LOGGER = logging.getLogger(__name__)


class VCSCredential(typing.NamedTuple):
    name: str
    type: str
    uri: str
    default_reference: str
    credential: str = ""
    public_key: str = ""

    @staticmethod
    def from_json(vcs: typing.Dict[str, str]) -> 'VCSCredential':
        """
        Convert raw dict from EDI to Model Deployment
        :param vcs: raw dict
        :return: a Model Deployment
        """
        vcs_spec = vcs.get('spec')
        vcs_metadata = vcs.get('metadata', {})

        return VCSCredential(
            name=vcs.get('name', vcs_metadata.get('name', '')),
            type=vcs_spec.get("type", ""),
            uri=vcs_spec.get("uri", ""),
            default_reference=vcs_spec.get("defaultReference", ""),
            credential=vcs_spec.get("credential", ""),
            public_key=vcs_spec.get("publicKey", "")
        )

    def to_json(self) -> typing.Dict[str, str]:
        """
        Convert a Model Deployment to raw json
        :return: raw dict
        """
        return {
            'name': self.name,
            'spec': {
                'type': self.type,
                'uri': self.uri,
                'defaultReference': self.default_reference,
                'credential': self.credential,
                'publicKey': self.public_key,
            }
        }


class VcsClient(RemoteEdiClient):
    """
    EDI client
    """

    def get(self, name: str) -> VCSCredential:
        """
        Get VCS Credential from EDI server

        :param name: VCS Credential name
        :type version: str
        :return: VCS Credential
        """
        return VCSCredential.from_json(self.query(f'{VCS_URL}/{name}'))

    def get_all(self) -> typing.List[VCSCredential]:
        """
        Get all VCS Credentials from EDI server

        :return: all VCS Credentials
        """
        return [VCSCredential.from_json(vcs) for vcs in self.query(VCS_URL)]

    def create(self, vcs: VCSCredential) -> str:
        """
        Create VCS Credential

        :param vcs: VCS Credential
        :return Message from EDI server
        """
        return self.query(VCS_URL, action='POST', payload=vcs.to_json())['message']

    def edit(self, vcs: VCSCredential) -> str:
        """
        Edit VCS Credential

        :param vcs: VCS Credential
        :return Message from EDI server
        """
        return self.query(VCS_URL, action='PUT', payload=vcs.to_json())['message']

    def delete(self, name: str) -> str:
        """
        Delete VCS Credentials

        :param name: Name of a VCS Credential
        :return Message from EDI server
        """
        return self.query(f'{VCS_URL}/{name}', action='DELETE')['message']


def build_client(args: argparse.Namespace = None) -> VcsClient:
    """
    Build VCS client from from ENV and from command line arguments

    :param args: (optional) command arguments with .namespace
    """
    host, token = None, None

    if args:
        if args.edi:
            host = args.edi

        if args.token:
            token = args.token

    if not host or not token:
        host = host or config.EDI_URL
        token = token or config.EDI_TOKEN

    if host:
        client = VcsClient(host, token)
    else:
        raise Exception('EDI endpoint is not configured')

    return client
