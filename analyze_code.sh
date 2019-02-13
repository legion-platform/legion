#!/bin/bash

set -e

pycodestyle --show-source --show-pep8 legion/legion
pycodestyle --show-source --show-pep8 legion/tests --ignore E402,E126,W503,E731
pydocstyle --source legion/legion

pycodestyle --show-source --show-pep8 legion_airflow/legion_airflow
pycodestyle --show-source --show-pep8 legion_airflow/tests
pydocstyle legion_airflow/legion_airflow

# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
touch legion/tests/__init__.py

TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/legion > legion-pylint.log
TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/tests >> legion-pylint.log

TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_airflow/legion_airflow >> legion-pylint.log
TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_airflow/tests >> legion-pylint.log
TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_test/legion_test >> legion-pylint.log
# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
rm -rf legion/tests/__init__.py

echo "Everything is ok"