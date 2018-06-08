#!/bin/bash

pycodestyle slack
pycodestyle tests
pydocstyle slack
pylint slack