#!/usr/bin/env python3
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
import setuptools

from jupyter_legion import __version__

data_files_spec = [
    ('etc/jupyter/jupyter_notebook_config.d',
     'jupyter-config/jupyter_notebook_config.d'),
]

setuptools.setup(
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
    packages=('jupyter_legion',),
    data_files=[('', ["README.md"])],
    zip_safe=False,
    install_requires=[
        'notebook',
        'legion-sdk',
        'pydantic'
    ],
    version=__version__
)