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
Cloud API requests and responses
"""
import typing
from pydantic import BaseModel

from legion.sdk.clients.training import ModelTraining
from legion.sdk.clients.deployment import ModelDeployment


class BasicNameRequest(BaseModel):
    """
    Basic request that contains only name
    """

    name: str


class FileInformationRequest(BaseModel):
    """
    Request to get information about file related to Git repository
    """

    path: str


class FileInformationResponse(BaseModel):
    """
    Response for FileInformationRequest request
    """

    path: str
    workDir: str
    extension: str
    gitCommandAvailable: bool = False
    fileInGitRepository: bool = False
    remotes: typing.List[str] = []
    references: typing.List[str] = []

    def to_json(self):
        """
        Convert to JSON

        :return: dict -- JSON-serializable dict
        """
        return {
            'path': self.path,
            'workDir': self.workDir,
            'extension': self.extension,
            'gitCommandAvailable': self.gitCommandAvailable,
            'fileInGitRepository': self.fileInGitRepository,
            'remotes': self.remotes,
            'references': self.references,
        }


class TrainingCreateRequest(BaseModel):
    """
    Request to create cloud training
    """

    name: str
    entrypoint: str
    image: str
    vcsName: str
    toolchain: str
    args: typing.List[str] = []
    reference: str = ''
    resources: typing.Mapping[str, typing.Any] = {}
    workDir: str = ''

    def convert_to_training(self) -> ModelTraining:
        """
        Convert to ModelTraining object

        :return: ModelTraining -- new object
        """
        return ModelTraining(
            name=self.name,
            toolchain_type=self.toolchain,
            entrypoint=self.entrypoint,
            args=self.args,
            resources=self.resources,
            vcs_name=self.vcsName,
            work_dir=self.workDir,
            reference=self.reference,
        )


class DeploymentCreateRequest(BaseModel):
    """
    Request to create cloud deployment
    """

    name: str
    image: str
    livenessProbeInitialDelay: int
    readinessProbeInitialDelay: int
    resources: typing.Mapping[str, typing.Any] = {}
    annotations: typing.Mapping[str, str] = {}

    def convert_to_deployment(self) -> ModelDeployment:
        """
        Convert to ModelDeployment object

        :return: ModelDeployment -- new object
        """
        return ModelDeployment(
            name=self.name,
            image=self.image,
            resources=self.resources,
            annotations=self.annotations,
            liveness_probe_initial_delay=self.livenessProbeInitialDelay,
            readiness_probe_initial_delay=self.livenessProbeInitialDelay
        )


class IssueTokenRequest(BaseModel):
    """
    Request to issue new model API token
    """

    # Role name
    role_name: str


class ApplyFromFileRequest(BaseModel):
    """
    Request to apply changes (create/edit/delete) from file
    """

    path: str
    removal: bool
