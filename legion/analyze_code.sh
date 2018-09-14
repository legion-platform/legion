#!/bin/bash

pycodestyle --show-source --show-pep8 legion
pycodestyle --show-source --show-pep8 tests --ignore E402,E126,W503,E731
pydocstyle --source legion
pylint legion