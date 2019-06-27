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
ROBOT_THREADS=6
CLUSTER_NAME=
PATH_TO_PROFILES_DIR=profiles
E2E_PYTHON_TAGS=
COMMIT_ID=
TEMP_DIRECTORY=
TAG=
# Example of DOCKER_REGISTRY: nexus.domain.com:443/
DOCKER_REGISTRY=
HELM_ADDITIONAL_PARAMS=
SANDBOX_IMAGE=legion/python-toolchain:latest
# Specify gcp auth keys
GOOGLE_APPLICATION_CREDENTIALS=

-include .env

.EXPORT_ALL_VARIABLES:

.PHONY: install-all install-cli install-services install-sdk

all: help

check-tag:
	@if [ "${TAG}" == "" ]; then \
	    echo "TAG is not defined, please define the TAG variable" ; exit 1 ;\
	fi
	@if [ "${DOCKER_REGISTRY}" == "" ]; then \
	    echo "DOCKER_REGISTRY is not defined, please define the DOCKER_REGISTRY variable" ; exit 1 ;\
	fi

## install-all: Install all python packages
install-all: install-sdk install-services install-cli install-python-toolchain install-jupyterlab-plugin install-robot

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

## install-jupyterlab-plugin: Install python package for JupyterLab
install-jupyterlab-plugin:
	cd legion/jupyterlab-plugin && \
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

## docker-build-pipeline-agent: Build pipeline agent docker image
docker-build-pipeline-agent:
	docker build -t legion/legion-pipeline-agent:latest -f containers/pipeline-agent/Dockerfile .

## docker-build-python-toolchain: Build python toolchain docker image
docker-build-python-toolchain:
	docker build -t legion/python-toolchain:latest -f containers/toolchains/python/Dockerfile .

## docker-build-edi: Build edi docker image
docker-build-edi:
	docker build --target edi -t legion/k8s-edi:latest -f containers/operator/Dockerfile .

## docker-build-edge: Build edge docker image
docker-build-edge:
	docker build -t legion/k8s-edge:latest -f containers/edge/Dockerfile .

## docker-build-model-builder: Build model builder docker image
docker-build-model-builder:
	docker build --target model-builder -t legion/k8s-model-builder:latest -f containers/operator/Dockerfile .

## docker-build-operator: Build operator docker image
docker-build-operator:
	docker build --target operator -t legion/k8s-operator:latest -f containers/operator/Dockerfile .

## docker-build-feedback-aggregator: Build feedback aggregator image
docker-build-feedback-aggregator:
	docker build --target server -t legion/k8s-feedback-aggregator:latest -f containers/feedback-aggregator/Dockerfile .

## docker-build-all: Build all docker images
docker-build-all:  docker-build-pipeline-agent  docker-build-python-toolchain  docker-build-edi  docker-build-edge  docker-build-model-builder  docker-build-operator  docker-build-feedback-aggregator

## docker-push-pipeline-agent: Push pipeline agent docker image
docker-push-pipeline-agent:
	docker tag legion/legion-pipeline-agent:latest ${DOCKER_REGISTRY}/legion/legion-pipeline-agent:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/legion-pipeline-agent:${TAG}

## docker-push-python-toolchain: Push python toolchain docker image
docker-push-python-toolchain:  check-tag
	docker tag legion/python-toolchain:latest ${DOCKER_REGISTRY}/legion/python-toolchain:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/python-toolchain:${TAG}

## docker-push-edge: Push edge docker image
docker-push-edge:  check-tag
	docker tag legion/k8s-edge:latest ${DOCKER_REGISTRY}/legion/k8s-edge:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-edge:${TAG}

## docker-push-edi: Push edi docker image
docker-push-edi:  check-tag
	docker tag legion/k8s-edi:latest ${DOCKER_REGISTRY}/legion/k8s-edi:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-edi:${TAG}

## docker-push-model-builder: Push model builder docker image
docker-push-model-builder:  check-tag
	docker tag legion/k8s-model-builder:latest ${DOCKER_REGISTRY}/legion/k8s-model-builder:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-model-builder:${TAG}

## docker-push-operator: Push operator docker image
docker-push-operator:  check-tag
	docker tag legion/k8s-operator:latest ${DOCKER_REGISTRY}/legion/k8s-operator:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-operator:${TAG}

## docker-push-feedback-aggregator: Push feedback aggregator docker image
docker-push-feedback-aggregator:  check-tag
	docker tag legion/k8s-feedback-aggregator:latest ${DOCKER_REGISTRY}legion/k8s-feedback-aggregator:${TAG}
	docker push ${DOCKER_REGISTRY}legion/k8s-feedback-aggregator:${TAG}

## docker-push-all: Push all docker images
docker-push-all:  docker-push-pipeline-agent  docker-push-python-toolchain  docker-push-edi  docker-push-edge  docker-push-model-builder  docker-push-operator  docker-push-feedback-aggregator

## helm-install: Install the legion helm chart from source code
helm-install:
	helm delete --purge legion || true
	helm install helms/legion --wait --timeout 60 --name legion --debug ${HELM_ADDITIONAL_PARAMS}

## install-unittests: Install unit tests
install-unittests:
	cd legion/tests/unit/requirements/ && pipenv install

## lint: Lints source code
lint:
	scripts/lint.sh

## build-docs: Build legion docs
build-docs:
	BUILD_VERSION="${LEGION_VERSION}" scripts/build-docs.sh

## unittests: Run unit tests
unittests:
	@if [ "${SANDBOX_PYTHON_TOOLCHAIN_IMAGE}" == "" ]; then \
	    docker build -t legion/python-toolchain:latest -f containers/toolchains/python/Dockerfile . ;\
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
	          --cover-xml-file=target/legion-cover.xml \
	          --cover-html \
	          --cover-html-dir=target/cover \
	          --logging-level DEBUG \
	          -v legion/tests/unit

## e2e-robot: Run e2e robot tests
e2e-robot:
	pabot --verbose --processes ${ROBOT_THREADS} \
	      -v PATH_TO_PROFILES_DIR:${PATH_TO_PROFILES_DIR} \
	      --listener legion.robot.process_reporter \
	      --outputdir target legion/tests/e2e/robot/tests/${ROBOT_FILES}

## e2e-python: Run e2e python tests
e2e-python:
	mkdir -p target
	nosetests ${E2E_PYTHON_TAGS} --with-xunitmp \
	          --logging-level DEBUG \
	          --xunitmp-file target/nosetests.xml \
	          -v legion/tests/e2e/python

## update-python-deps: Update all python dependecies in the Pipfiles
update-python-deps:
	scripts/update_python_deps.sh

## run-sandbox: Start Python toolchain sandbox
run-sandbox:
	rm -rf ./legion-activate.sh
	legionctl create-sandbox --image ${SANDBOX_IMAGE}

	./legion-activate.sh

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
