#!/bin/bash

set -e

pydocstyle --source legion/legion

# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
touch legion/tests/__init__.py

TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/legion > legion-pylint.log
TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/tests >> legion-pylint.log

TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_test/legion_test >> legion-pylint.log
# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
rm -rf legion/tests/__init__.py

echo "PyLint warnings:"
cat legion-pylint.log
