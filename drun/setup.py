from setuptools import setup


def extract_requirements(filename):
    """
    Extracts requirements from a pip formatted requirements file.
    """
    with open(filename, 'r') as requirements_file:
        return requirements_file.read().splitlines()

setup(name='drun',
      version='0.5',
      description='Legion server',
      url='http://github.com/akharlamov/drun-root',
      author='Alexey Kharlamov',
      author_email='alexey@kharlamov.biz',
      license='Apache v2',
      packages=['drun'],
      include_package_data=True,
      scripts=['bin/legion'],

      install_requires=[
          'dill',
          'python-interface',
          'pandas',
          'traitlets',
          'docker',
          'python-consul',
          'flask',
          'docker',
          'numpy'
      ],
      test_suite='nose.collector',
      tests_require=[
          'unittest2',
          'nose'
      ],
      zip_safe=False)
