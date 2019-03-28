SHELL := /bin/bash

PROJECTNAME := $(shell basename "$(PWD)")
PYLINT_FOLDER=target/pylint
PYDOCSTYLE_FOLDER=target/pydocstyle
PROJECTS_PYLINT=sdk cli services toolchain tests
PROJECTS_PYCODESTYLE="sdk cli services toolchain"
BUILD_PARAMS=
LEGION_VERSION=0.11.0
SANDBOX_PYTHON_TOOLCHAIN_IMAGE=
CREDENTIAL_SECRETS=.secrets.yaml
ROBOT_FILES=**/*.robot
CLUSTER_NAME=
PATH_TO_PROFILES_DIR=deploy/profiles
E2E_PYTHON_TAGS=
COMMIT_ID=

-include .env

.EXPORT_ALL_VARIABLES:

.PHONY: install-all install-cli install-services install-sdk

all: install-all

install-all: install-sdk install-services install-cli install-python-toolchain install-robot

## install-sdk: Install sdk python package
install-sdk:
	cd legion/sdk && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-cli: Install cli python package
install-cli:
	cd legion/cli && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-services: Install services python package
install-services:
	cd legion/services && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-python-toolchain: Install python toolchain
install-python-toolchain:
	cd legion/toolchains/python && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-robot: Install robot tests
install-robot:
	cd legion/robot && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

docker-pipeline:
	docker build -t legionplatform/python-pipeline:latest -f containers/pipeline/Dockerfile .

docker-python-toolchain:
	docker build -t legionplatform/python-toolchain:latest -f containers/toolchains/python/Dockerfile .

docker-ansible:
	docker build -t legionplatform/k8s-ansible:latest -f containers/ansible/Dockerfile .

docker-edi:
	docker build -t legionplatform/k8s-edi:latest -f containers/edi/Dockerfile .

docker-edge:
	docker build -t legionplatform/k8s-edge:latest -f containers/edge/Dockerfile .

## install-unittests: Install unit tests
install-unittests:
	pip3 install -e legion/tests

## lint: Lints source code
lint:
	scripts/lint.sh

build-docs:
	BUILD_VERSION="${LEGION_VERSION}" scripts/build-docs.sh

## unittests: Run unit tests
unittests:
	@if [ "${SANDBOX_PYTHON_TOOLCHAIN_IMAGE}" == "" ]; then \
	    docker build -t legionplatform/python-toolchain:latest -f containers/toolchains/python/Dockerfile . ;\
	fi

	mkdir -p target
	mkdir -p target/cover

	DEBUG=true VERBOSE=true nosetests --processes=10 \
	          --process-timeout=600 \
	          --with-coverage \
	          --cover-package legion \
	          --with-xunitmp \
	          --xunitmp-file target/nosetests.xml \
	          --cover-xml \
	          --cover-xml-file=target/coverage.xml \
	          --cover-html \
	          --cover-html-dir=target/cover \
	          --logging-level DEBUG \
	          -v legion/tests/unit

## e2e-robot: Run e2e robot tests
e2e-robot:
	pabot --verbose --processes 6 \
	      -v PATH_TO_PROFILES_DIR:profiles \
	      --listener legion.robot.process_reporter \
	      --outputdir target legion/tests/e2e/robot/tests/${ROBOT_FILES}

## e2e-python: Run e2e python tests
e2e-python:
	mkdir -p target
	nosetests ${E2E_PYTHON_TAGS} --with-xunit \
	          --logging-level DEBUG \
	          --xunitmp-file target/nosetests.xml \
	          -v legion/tests/e2e/python

create-models-job:
	create_example_jobs \
	     "https://jenkins.${CLUSTER_NAME}" \
	     ./examples \
	     ./ \
	     "https://github.com/legion-platform/legion.git" \
	     ${COMMIT_ID} \
	     --connection-timeout 600 \
	     --git-root-key "legion-root-key" \
	     --model-host "" \
	     --dynamic-model-prefix "DYNAMIC MODEL" \
	     --profiles-dir deploy/profiles \
	     --profile ${CLUSTER_NAME}

update-python-deps:
	./scripts/update_python_deps.sh

help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
