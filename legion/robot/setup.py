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
import json
import os
import re
import typing

from setuptools import setup, find_namespace_packages

PIPFILE_DEP_SECTION = 'default'
PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PIP_FILE_LOCK_PATH = os.path.join(PACKAGE_ROOT_PATH, 'Pipfile.lock')
VERSION_FILE = os.path.join(PACKAGE_ROOT_PATH, 'legion/robot', 'version.py')


def extract_requirements() -> typing.List[str]:
    """
    Extracts requirements from a pip formatted requirements file.

    :return: package names as strings
    """
    legion_dependencies = [f'legion-services=={extract_version()}']

    with open(PIP_FILE_LOCK_PATH, 'r') as pip_file_lock_stream:
        pip_file_lock_data = json.load(pip_file_lock_stream)
        pip_file_section_data = pip_file_lock_data.get(PIPFILE_DEP_SECTION, {})
        return legion_dependencies + [
            key + value['version']
            for (key, value)
            in pip_file_section_data.items()
        ]


def extract_version() -> str:
    """
    Extract version from .py file using regex

    :return: legion version
    """
    with open(VERSION_FILE, 'rt') as version_file:
        file_content = version_file.read()
        VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
        mo = re.search(VSRE, file_content, re.M)
        if mo:
            return mo.group(1)
        else:
            raise RuntimeError("Unable to find version string in %s." % (file_content,))


setup(
    name='legion-robot',
    version=extract_version(),
    description='Legion robotframework libraries',
    packages=find_namespace_packages(),
    url='https://github.com/legion-platform/legion',
    author='Alexey Kharlamov, Kirill Makhonin',
    author_email='alexey@kharlamov.biz, kirill@makhonin.biz',
    license='Apache v2',
    entry_points={
        'console_scripts': ['create_example_jobs=legion.robot.entrypoints.create_example_jobs:main'],
    },
    install_requires=extract_requirements()
)
