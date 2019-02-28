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

from setuptools import setup


PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_LIB_PATH = os.path.join(PACKAGE_ROOT_PATH, 'legion_core')

PIP_FILE_LOCK_PATH = os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'Pipfile.lock')


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
    with open(filename, 'rt') as version_file:
        file_content = version_file.read()
        VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
        mo = re.search(VSRE, file_content, re.M)
        if mo:
            return mo.group(1)
        else:
            raise RuntimeError("Unable to find version string in %s." % (file_content,))


def extract_package_with_version(package_name, filename):
    version = extract_version(filename)
    return '{}=={}'.format(package_name, version)


setup(name='legion-core',
      version=extract_version(os.path.join(PACKAGE_ROOT_PATH, os.path.pardir, 'version.py')),
      description='Legion core package',
      url='http://github.com/akharlamov/legion-root',
      author='Alexey Kharlamov, Kirill Makhonin',
      author_email='alexey@kharlamov.biz, kirill@makhonin.biz',
      license='Apache v2',
      packages=['legion.core'],
      include_package_data=True,
      install_requires=extract_requirements(PIP_FILE_LOCK_PATH, 'default'),
      extras_require={
          'cli': [
              extract_package_with_version('legion-cli',
                                           os.path.join(PACKAGE_ROOT_PATH, os.path.pardir, 'version.py'))
          ],
          'services': [
              extract_package_with_version('legion-services',
                                           os.path.join(PACKAGE_ROOT_PATH, os.path.pardir, 'version.py'))
          ]
      },
      test_suite='nose.collector',
      tests_require=extract_requirements(PIP_FILE_LOCK_PATH, 'develop'),
      zip_safe=False)
