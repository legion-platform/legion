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


class BasicIdRequest(BaseModel):
    """
    Basic request that contains only name
    """

    id: str


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


class ApplyFromFileRequest(BaseModel):
    """
    Request to apply changes (create/edit/delete) from file
    """

    path: str
    removal: bool
