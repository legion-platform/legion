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
from legion.sdk.definitions import MODEL_TRAINING_URL

LOGGER = logging.getLogger(__name__)
TRAINING_SUCCESS_STATE = "succeeded"
TRAINING_FAILED_STATE = "failed"


# TODO: Currently we support only part of fields.
# Add rest part after migration to golang
class ModelTraining(typing.NamedTuple):
    name: str
    toolchain_type: str
    entrypoint: str
    args: typing.List[str] = []
    resources: typing.Mapping[str, typing.Any] = {}
    vcs_name: str = ""
    work_dir: str = ""
    reference: str = ""
    model_id: str = ""
    model_version: str = ""
    state: str = ""
    trained_image: str = ""

    @staticmethod
    def from_json(mt: typing.Dict[str, str]) -> 'ModelTraining':
        """
        Convert raw dict from EDI to Model Training
        :param mt: raw dict
        :return: a Model Training
        """
        mt_spec = mt.get('spec', {})
        mt_metadata = mt.get('metadata', {})
        mt_status = mt.get('status', {})

        return ModelTraining(
            name=mt.get('name', mt_metadata.get('name')),
            toolchain_type=mt_spec.get('toolchain', ''),
            resources=mt_spec.get('resources', {}),
            entrypoint=mt_spec.get('entrypoint', ''),
            args=mt_spec.get('args', []),
            vcs_name=mt_spec.get('vcsName', ''),
            work_dir=mt_spec.get('workDir', ''),
            reference=mt_spec.get('reference', ''),
            model_id=mt_status.get('id', ''),
            model_version=mt_status.get('version', ''),
            state=mt_status.get('state', ''),
            trained_image=mt_status.get('modelImage', '')
        )

    def to_json(self, with_status=False) -> typing.Dict[str, str]:
        """
        Convert a Model Training to raw json
        :param with_status: add status fields
        :return: raw dict
        """
        result = {
            'name': self.name,
            'spec': {
                'toolchain': self.toolchain_type,
                'resources': self.resources,
                'entrypoint': self.entrypoint,
                'args': self.args,
                'vcsName': self.vcs_name,
                'workDir': self.work_dir,
                'reference': self.reference
            }
        }
        if with_status:
            result['status'] = {
                'id': self.model_id,
                'version': self.model_version,
                'state': self.state,
                'modelImage': self.trained_image
            }
        return result


class ModelTrainingClient(RemoteEdiClient):
    """
    EDI client
    """

    def get(self, name: str) -> ModelTraining:
        """
        Get Model Training from EDI server

        :param name: Model Training name
        :type version: str
        :return: Model Training
        """
        return ModelTraining.from_json(self.query(f'{MODEL_TRAINING_URL}/{name}'))

    def get_all(self) -> typing.List[ModelTraining]:
        """
        Get all Model Trainings from EDI server

        :return: all Model Trainings
        """
        return [ModelTraining.from_json(mt) for mt in self.query(MODEL_TRAINING_URL)]

    def create(self, mt: ModelTraining) -> str:
        """
        Create Model Training

        :param mt: Model Training
        :return Message from EDI server
        """
        return self.query(MODEL_TRAINING_URL, action='POST', payload=mt.to_json())['message']

    def edit(self, mt: ModelTraining) -> str:
        """
        Edit Model Training

        :param mt: Model Training
        :return Message from EDI server
        """
        return self.query(MODEL_TRAINING_URL, action='PUT', payload=mt.to_json())['message']

    def delete(self, name: str) -> str:
        """
        Delete Model Trainings

        :param name: Name of a Model Training
        :return Message from EDI server
        """
        return self.query(f'{MODEL_TRAINING_URL}/{name}', action='DELETE')['message']

    def log(self, name: str, follow: bool = False) -> str:
        """
        Stream logs from training

        :param follow: follow stream
        :param name: Name of a Model Training
        :return Message from EDI server
        """
        return self.stream(f'{MODEL_TRAINING_URL}/{name}/log', 'GET', params={'follow': follow})


def build_client(args: argparse.Namespace = None) -> ModelTrainingClient:
    """
    Build Model training client from from ENV and from command line arguments

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
        client = ModelTrainingClient(host, token)
    else:
        raise Exception('EDI endpoint is not configured')

    return client
