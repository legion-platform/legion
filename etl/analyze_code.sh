#!/bin/bash

pycodestyle etl
pycodestyle tests
pydocstyle etl
pylint etl