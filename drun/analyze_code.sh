#!/bin/bash

pycodestyle drun
pycodestyle tests
pydocstyle drun
pylint drun