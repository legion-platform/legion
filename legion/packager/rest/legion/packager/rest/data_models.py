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
Data models (validation by pydantic)
"""
import typing

import pydantic


class LegionProjectManifestBinaries(pydantic.BaseModel):
    """
    Legion Project Manifest's Binaries description
    """

    type: str
    dependencies: str
    conda_path: typing.Optional[str]


class LegionProjectManifestModel(pydantic.BaseModel):
    """
    Legion Project Manifest's Model description
    """

    name: str
    version: str
    workDir: str
    entrypoint: str


class LegionProjectManifestToolchain(pydantic.BaseModel):
    """
    Legion Project Manifest's Toolchain description
    """

    name: str
    version: str


class LegionProjectManifest(pydantic.BaseModel):
    """
    Legion Project Manifest description class
    """

    binaries: LegionProjectManifestBinaries
    model: typing.Optional[LegionProjectManifestModel]
    legionVersion: typing.Optional[str]
    toolchain: typing.Optional[LegionProjectManifestToolchain]


class PackagingResourceArguments(pydantic.BaseModel):
    """
    Legion Packaging Resource Arguments
    """

    dockerfilePush: bool = True
    dockerfileAddCondaInstallation: bool = True
    dockerfileBaseImage: str = 'python:3.6'
    dockerfileCondaEnvsLocation: str = '/opt/conda/envs/'
    host: str = '0.0.0.0'
    port: int = 5000
    timeout: int = 60
    workers: int = 1
    threads: int = 4
