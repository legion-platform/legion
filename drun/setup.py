from setuptools import setup
import os
import re

PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


def extract_requirements(filename):
    """
    Extracts requirements from a pip formatted requirements file.
    :param filename: str path to file
    :return: list of package names as strings
    """
    with open(filename, 'r') as requirements_file:
        return requirements_file.read().splitlines()


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


setup(name='drun',
      version=extract_version(os.path.join(PACKAGE_ROOT_PATH, 'drun', 'version.py')),
      description='Legion server',
      url='http://github.com/akharlamov/drun-root',
      author='Alexey Kharlamov',
      author_email='alexey@kharlamov.biz',
      license='Apache v2',
      packages=['drun'],
      include_package_data=True,
      scripts=['bin/legion'],
      install_requires=extract_requirements(os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'base.txt')),
      test_suite='nose.collector',
      tests_require=extract_requirements(os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'test.txt')),
      zip_safe=False)
