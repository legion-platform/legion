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
import os
import re
import json
import shutil

from setuptools import setup
from distutils import log as dist_logger
from distutils.core import Command


PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_LIB_PATH = os.path.join(PACKAGE_ROOT_PATH, 'legion')

PIP_FILE_LOCK_PATH = os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'Pipfile.lock')
DATA_DIRECTORY = os.path.join(PACKAGE_LIB_PATH, 'data')


class CollectDataBuildCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def copy_file(self, src, *target_path):
        target_path = os.path.join(DATA_DIRECTORY, *target_path)
        dist_logger.info('copying %s to %s', src, target_path)
        shutil.copyfile(src, target_path)

    def run(self):
        dist_logger.info('collecting requirements data to %s', DATA_DIRECTORY)
        if os.path.exists(DATA_DIRECTORY):
            dist_logger.info('removing existed directory')
            shutil.rmtree(DATA_DIRECTORY)

        dist_logger.info('creating directory')
        os.makedirs(DATA_DIRECTORY)

        dist_logger.info('copying data')
        self.copy_file(PIP_FILE_LOCK_PATH, 'Pipfile.lock')

        dist_logger.info('collection of requirements has been finished')


cmdclass = dict(
    collect_data=CollectDataBuildCommand
)


def extract_requirements(pip_file_lock_path, section):
    """
    Extracts requirements from a pip formatted requirements file.

    :param pip_file_lock_path: path to Pipfile.lock
    :type pip_file_lock_path: str
    :param section: name of package section in Pipfile.lock
    :type section: str
    :return: list[str] of package names as strings
    """
    with open(pip_file_lock_path, 'r') as pip_file_lock_stream:
        pip_file_lock_data = json.load(pip_file_lock_stream)
        pip_file_section_data = pip_file_lock_data.get(section, {})
        return [
            key + value['version']
            for (key, value)
            in pip_file_section_data.items()
        ]


def extract_version(filename):
    """
    Extract version from .py file using regex
    :param filename: str path to file
    :return: str version
    """
    with open(filename, 'r') as version_file:
        file_content = open(filename, "rt").read()
        VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
        mo = re.search(VSRE, file_content, re.M)
        if mo:
            return mo.group(1)
        else:
            raise RuntimeError("Unable to find version string in %s." % (file_content,))


setup(name='legion',
      version=extract_version(os.path.join(PACKAGE_ROOT_PATH, 'legion', 'version.py')),
      description='Legion',
      url='http://github.com/akharlamov/legion-root',
      author='Alexey Kharlamov, Kirill Makhonin',
      author_email='alexey@kharlamov.biz, kirill@makhonin.biz',
      license='Apache v2',
      packages=['legion'],
      include_package_data=True,
      scripts=['bin/legionctl', 'bin/edi', 'bin/legion-template'],
      package_data={'legion': ['legion/data/*']},
      install_requires=extract_requirements(PIP_FILE_LOCK_PATH, 'default'),
      test_suite='nose.collector',
      tests_require=extract_requirements(PIP_FILE_LOCK_PATH, 'develop'),
      zip_safe=False,
      cmdclass=cmdclass)
