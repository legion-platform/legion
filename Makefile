SHELL := /bin/bash

PROJECTNAME := $(shell basename "$(PWD)")
PYLINT_FOLDER=target/pylint
PYDOCSTYLE_FOLDER=target/pydocstyle
PROJECTS_PYLINT=sdk cli tests
PROJECTS_PYCODESTYLE="sdk cli"
BUILD_PARAMS=
LEGION_VERSION=0.11.0
CREDENTIAL_SECRETS=.secrets.yaml
SANDBOX_PYTHON_TOOLCHAIN_IMAGE=
ROBOT_FILES=**/*.robot
ROBOT_THREADS=6
ROBOT_OPTIONS=-e disable
CLUSTER_NAME=
E2E_PYTHON_TAGS=
COMMIT_ID=
TEMP_DIRECTORY=
BUILD_TAG=latest
TAG=
# Example of DOCKER_REGISTRY: nexus.domain.com:443/
DOCKER_REGISTRY=
HELM_ADDITIONAL_PARAMS=
# Specify gcp auth keys
GOOGLE_APPLICATION_CREDENTIALS=
MOCKS_DIR=target/mocks
SWAGGER_FILE=legion/operator/docs/swagger.yaml
TS_MODEL_DIR=legion/jupyterlab-plugin/src/legion
PYTHON_MODEL_DIR=legion/sdk/legion/sdk/models
SWAGGER_CODEGEN_BIN=java -jar swagger-codegen-cli.jar

HIERA_KEYS_DIR=
LEGION_PROFILES_DIR=

CLUSTER_NAME=
CLOUD_PROVIDER=

EXPORT_HIERA_DOCKER_IMAGE := legion/k8s-terraform:${BUILD_TAG}
SECRET_DIR := $(CURDIR)/.secrets
CLUSTER_PROFILE := ${SECRET_DIR}/cluster_profile.json

-include .env

.EXPORT_ALL_VARIABLES:

.PHONY: install-all install-cli install-sdk

all: help

check-tag:
	@if [ "${TAG}" == "" ]; then \
	    echo "TAG is not defined, please define the TAG variable" ; exit 1 ;\
	fi
	@if [ "${DOCKER_REGISTRY}" == "" ]; then \
	    echo "DOCKER_REGISTRY is not defined, please define the DOCKER_REGISTRY variable" ; exit 1 ;\
	fi

## install-all: Install all python packages
install-all: install-sdk install-cli install-jupyterlab-plugin install-robot install-rest-packager

## install-sdk: Install sdk python package
install-sdk:
	cd legion/sdk && \
		rm -rf build dist *.egg-info && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-cli: Install cli python package
install-cli:
	cd legion/cli && \
		rm -rf build dist *.egg-info && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-jupyterlab-plugin: Install python package for JupyterLab
install-jupyterlab-plugin:
	cd legion/jupyterlab-plugin && \
		rm -rf build dist *.egg-info && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-rest-packager: Install REST packager
install-rest-packager:
	cd legion/packager/rest && \
		rm -rf build dist *.egg-info && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## install-robot: Install robot tests
install-robot:
	cd legion/robot && \
		rm -rf build dist *.egg-info && \
		pip3 install ${BUILD_PARAMS} -e . && \
		python setup.py sdist && \
    	python setup.py bdist_wheel

## docker-build-pipeline-agent: Build pipeline agent docker image
docker-build-pipeline-agent:
	docker build -t legion/legion-pipeline-agent:${BUILD_TAG} -f containers/pipeline-agent/Dockerfile .

## docker-build-python-toolchain: Build python toolchain docker image
docker-build-jupyterlab:
	docker build -t legion/jupyterlab:${BUILD_TAG} -f containers/jupyterlab/Dockerfile .

## docker-build-rest-packager: Build REST packager docker image
docker-build-rest-packager:
	docker build -t legion/packager-rest:${BUILD_TAG} -f containers/ai-packagers/rest/Dockerfile .

## docker-build-edi: Build edi docker image
docker-build-edi:
	docker build --target edi -t legion/k8s-edi:${BUILD_TAG} -f containers/operator/Dockerfile .

## docker-build-model-builder: Build model builder docker image
docker-build-model-builder:
	docker build --target model-builder -t legion/k8s-model-builder:${BUILD_TAG} -f containers/operator/Dockerfile .

## docker-build-model-packager: Build model packager docker image
docker-build-model-packager:
	docker build --target model-packager -t legion/k8s-model-packager:${BUILD_TAG} -f containers/operator/Dockerfile .

## docker-build-operator: Build operator docker image
docker-build-operator:
	docker build --target operator -t legion/k8s-operator:${BUILD_TAG} -f containers/operator/Dockerfile .

## docker-build-feedback-aggregator: Build feedback aggregator image
docker-build-feedback-aggregator:
	docker build --target server -t legion/k8s-feedback-aggregator:${BUILD_TAG} -f containers/feedback-aggregator/Dockerfile .

## docker-build-all: Build all docker images
docker-build-all:  docker-build-pipeline-agent docker-build-jupyterlab docker-build-edi  docker-build-model-builder  docker-build-operator  docker-build-feedback-aggregator

## docker-push-pipeline-agent: Push pipeline agent docker image
docker-push-pipeline-agent:
	docker tag legion/legion-pipeline-agent:${BUILD_TAG} ${DOCKER_REGISTRY}/legion/legion-pipeline-agent:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/legion-pipeline-agent:${TAG}

## docker-push-jupyterlab: Push python toolchain docker image
docker-push-jupyterlab:  check-tag
	docker tag legion/jupyterlab:${BUILD_TAG} ${DOCKER_REGISTRY}/legion/jupyterlab:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/jupyterlab:${TAG}

## docker-push-edi: Push edi docker image
docker-push-edi:  check-tag
	docker tag legion/k8s-edi:${BUILD_TAG} ${DOCKER_REGISTRY}/legion/k8s-edi:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-edi:${TAG}

## docker-push-model-builder: Push model builder docker image
docker-push-model-builder:  check-tag
	docker tag legion/k8s-model-builder:${BUILD_TAG} ${DOCKER_REGISTRY}/legion/k8s-model-builder:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-model-builder:${TAG}

## docker-push-operator: Push operator docker image
docker-push-operator:  check-tag
	docker tag legion/k8s-operator:${BUILD_TAG} ${DOCKER_REGISTRY}/legion/k8s-operator:${TAG}
	docker push ${DOCKER_REGISTRY}/legion/k8s-operator:${TAG}

## docker-push-feedback-aggregator: Push feedback aggregator docker image
docker-push-feedback-aggregator:  check-tag
	docker tag legion/k8s-feedback-aggregator:${BUILD_TAG} ${DOCKER_REGISTRY}legion/k8s-feedback-aggregator:${TAG}
	docker push ${DOCKER_REGISTRY}legion/k8s-feedback-aggregator:${TAG}

## docker-push-all: Push all docker images
docker-push-all:  docker-push-pipeline-agent docker-push-jupyterlab docker-push-edi  docker-push-model-builder  docker-push-operator  docker-push-feedback-aggregator

## helm-install: Install the legion helm chart from source code
helm-install: helm-delete
	helm install helms/legion --atomic --wait --timeout 320 --namespace legion --name legion --debug ${HELM_ADDITIONAL_PARAMS}

## helm-delete: Delete the legion helm release
helm-delete:
	helm delete --purge legion || true

## install-unittests: Install unit tests
install-unittests:
	cd legion/tests/unit/requirements/ && pipenv install

## lint: Lints source code
lint:
	scripts/lint.sh

## build-docs: Build legion docs
build-docs: build-docs-builder
	docker run --rm -v $(PWD)/docs:/var/docs  -v $(PWD):/legion-sources --workdir /var/docs legion/docs-builder:latest /generate.sh


## build-docs-builder: Build docker image that can build documentation
build-docs-builder:
	docker build -t legion/docs-builder:latest -f containers/docs-builder/Dockerfile .

## generate-python-client: Generate python models
generate-python-client:
	mkdir -p ${MOCKS_DIR}
	rm -rf ${MOCKS_DIR}/python
	$(SWAGGER_CODEGEN_BIN) generate \
		-i ${SWAGGER_FILE} \
		-l python-flask \
		-o ${MOCKS_DIR}/python \
		--model-package sdk.models \
		-c scripts/swagger/python.conf.json
	# bug in swagger generator
	mv ${MOCKS_DIR}/python/legion/sdk.models/* ${MOCKS_DIR}/python/legion/sdk/models/

	# replace the util script location
	sed -i 's/from legion import util/from legion.sdk.models import util/g' ${MOCKS_DIR}/python/legion/sdk/models/*
	mv ${MOCKS_DIR}/python/legion/util.py ${MOCKS_DIR}/python/legion/sdk/models/

	rm -rf ${PYTHON_MODEL_DIR}
	mkdir -p ${PYTHON_MODEL_DIR}
	cp -r ${MOCKS_DIR}/python/legion/sdk/models/* ${PYTHON_MODEL_DIR}
	git add ${PYTHON_MODEL_DIR}

## generate-ts-client: Generate typescript models
generate-ts-client:
	mkdir -p ${MOCKS_DIR}
	rm -rf ${MOCKS_DIR}/ts
	$(SWAGGER_CODEGEN_BIN) generate \
		-i ${SWAGGER_FILE} \
		-l typescript-jquery \
		-o ${MOCKS_DIR}/ts \
		--model-package legion

	rm -rf ${TS_MODEL_DIR}
	mkdir -p ${TS_MODEL_DIR}
	cp -r ${MOCKS_DIR}/ts/legion/* ${TS_MODEL_DIR}
	git add ${TS_MODEL_DIR}

## generate-clients: Generate all models
generate-clients: generate-python-client generate-ts-client

## unittests: Run unit tests
unittests:
	mkdir -p target
	mkdir -p target/cover
	DEBUG=true VERBOSE=true pytest \
	          --cov=legion \
	          --cov-report xml:target/legion-cover.xml \
	          --cov-report html:target/cover \
	          --cov-report term-missing \
	          --junitxml=target/nosetests.xml \
	          legion

## setup-e2e-robot: Prepare a test data for the e2e robot tests
setup-e2e-robot:
	legion-authenticate-test-user ${CLUSTER_PROFILE}

	./legion/tests/stuff/training_stuff.sh setup

## cleanup-e2e-robot: Delete a test data after the e2e robot tests
cleanup-e2e-robot:
	legion-authenticate-test-user ${CLUSTER_PROFILE}

	./legion/tests/stuff/training_stuff.sh cleanup

## e2e-robot: Run e2e robot tests
e2e-robot:
	pabot --verbose --processes ${ROBOT_THREADS} \
	      -v CLUSTER_PROFILE:${CLUSTER_PROFILE} \
	      --listener legion.robot.process_reporter \
	      --outputdir target legion/tests/e2e/robot/tests/${ROBOT_FILES}

## update-python-deps: Update all python dependecies in the Pipfiles
update-python-deps:
	scripts/update_python_deps.sh

## run-sandbox: Start Python toolchain sandbox
run-sandbox:
	legionctl sandbox --image legion/jupyterlab:${BUILD_TAG}

	./legion-activate.sh

define verify_existence
	@if [ "${$(1)}" == "" ]; then \
	    echo "$(1) is not found, please define the $(1) variable" ; exit 1 ;\
	fi
endef

## export-hiera: Export hiera data
export-hiera:
	set -e
	$(call verify_existence,CLUSTER_NAME)
	$(call verify_existence,HIERA_KEYS_DIR)
	$(call verify_existence,SECRET_DIR)
	$(call verify_existence,CLOUD_PROVIDER)
	$(call verify_existence,EXPORT_HIERA_DOCKER_IMAGE)
	$(call verify_existence,LEGION_PROFILES_DIR)

	mkdir -p ${SECRET_DIR}
	docker run \
	           --net host \
	           -v ${HIERA_KEYS_DIR}:/opt/legion/.hiera_keys \
	           -v ${LEGION_PROFILES_DIR}:/opt/legion/legion-profiles \
	           -v ${SECRET_DIR}:/opt/legion/.secrets \
	           -e CLUSTER_NAME=${CLUSTER_NAME} \
	           -e CLOUD_PROVIDER=${CLOUD_PROVIDER} \
	           ${EXPORT_HIERA_DOCKER_IMAGE} hiera_exporter_helper

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
