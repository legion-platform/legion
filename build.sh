#!/usr/bin/env bash

cd base-python-image
docker build -t drun/base-python-image:latest .
cd ..

cd jenkins
docker build -t drun/jenkins-server:latest .
cd ..
