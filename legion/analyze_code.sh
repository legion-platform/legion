#!/bin/bash

pycodestyle --show-source --show-pep8 legion --ignore W1202
pycodestyle --show-source --show-pep8 tests --ignore E402,E126,W503,E731,W1202
pydocstyle --source legion
pylint legion