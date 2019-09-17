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

data_files_spec = [
    ('etc/jupyter/jupyter_notebook_config.d',
     'jupyter-config/jupyter_notebook_config.d'),
]

PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(PACKAGE_ROOT_PATH, 'legion/jupyterlab', 'version.py')


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
    name='jupyter_legion',
    description='A JupyterLab Notebook server extension for jupyter_legion',
    author='Legion Platform Team',
    license='Apache v2',

    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='jupyter jupyterlab',
    python_requires='>=3.6',
    packages=find_namespace_packages(),
    data_files=[('', ["README.md"])],
    zip_safe=False,
    version=extract_version(),
    install_requires=requirements
)
