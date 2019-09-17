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
import os
import re

from setuptools import find_namespace_packages, setup

PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(PACKAGE_ROOT_PATH, 'legion/cli', 'version.py')


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


with open('requirements.txt') as f:
    requirements = [f'legion-sdk=={extract_version()}'] + f.read().splitlines()

setup(
    name='legion-cli',
    version=extract_version(),
    description='Legion CLI',
    packages=find_namespace_packages(),
    url='https://github.com/legion-platform/legion',
    author='Alexey Kharlamov, Kirill Makhonin',
    author_email='alexey@kharlamov.biz, kirill@makhonin.biz',
    license='Apache v2',
    entry_points={
        'console_scripts': ['legionctl=legion.cli.main:main'],
    },
    install_requires=requirements,
)
