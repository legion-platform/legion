#!/bin/bash

pycodestyle legion_airflow
pycodestyle tests
pydocstyle legion_airflow
pylint legion_airflow