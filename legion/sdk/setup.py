import json
import os
import re

from setuptools import setup, find_namespace_packages

PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PIP_FILE_LOCK_PATH = os.path.join(PACKAGE_ROOT_PATH, 'Pipfile.lock')


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


setup(
    name='legion-sdk',
    version=extract_version(os.path.join(PACKAGE_ROOT_PATH, 'legion/sdk', 'version.py')),
    description='Legion',
    packages=find_namespace_packages(),
    url='https://github.com/legion-platform/legion',
    author='Alexey Kharlamov, Kirill Makhonin',
    author_email='alexey@kharlamov.biz, kirill@makhonin.biz',
    license='Apache v2',
    install_requires=extract_requirements(PIP_FILE_LOCK_PATH, 'default'),
)
