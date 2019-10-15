# Development hints

## Set up a development environment

Legion product contains 5 main development parts:
* Python packages
    * Executes the `make install-all` command to downloads all dependencies and install Legion python packages.
    * Verifies that the command finished successfully, for example: `legionctl --version`
    * Main entrypoints:
      * Legion sdk - `legion/sdk`
      * Legion cli - `legion/cli`
* Legion Jupiterlab plugin
    * Workdir is `legion/jupyterlab-plugin`
    * Executes the `yarn install` command to downloads all Javascripts dependencies.
    * Executes the `npm run build && jupyter labextension install` command to build the Jupiterlab plugin.
    * Starts the Jyputerlab server using `jupyter lab` command.
    * Or you can perform all actions above using docker, for example: `make docker-build-jupyterlab && make run-sandbox`
* Golang services:
    * Executes the `dep ensure` command in the `legion/operator` directory to downloads all dependencies.
    * Executes the `make build-all` command in the `legion/operator` to build all Golang services.
    * Main entrypoints:
      * API Gateway service - `legion/operator/cmd/edi/main.go`
      * Kubernetes operator - `legion/operator/cmd/operator/main.go`
      * AI Trainer - `legion/operator/cmd/trainer/main.go`
      * AI Packager - `legion/operator/cmd/packager/main.go`
      * Service catalog - `legion/operator/cmd/service_catalog/main.go`
* Legion Mlflow integration
    * Executes the `pip install -e .` command in the `legion-mlflow` repository.
* Legion Airflow plugin
    * Executes the `pip install -e .` command in the `legion-airflow-plugins` repository.

## Update dependencies

* `Python`. Update dependencies in a `Pipfile`. Execute `make update-python-deps` command.

* `Golang`. Update dependencies in a `Gopkg.toml`. Execute `dep ensure` command in `legion/operator` directory.

* `Typescript`. Legion uses the `yarn` to manipulate the typescript dependencies. 

## Make changes in API entities

All API entities are located in `legion/operator/pkg/api` directory.

To generate swagger documentation execute `make generate-all` in `legion/operator` directory. 
Important for Mac users: Makefile uses GNU `sed` tool, but MacOS uses BSD `sed` by default. They are not fully 
compatible. So you need install and use GNU `sed` on your Mac for using Makefile.

After previous action you can update python and typescript clients using the following command: `make generate-clients`.

## Actions before a pull request

Make sure you have done the following actions before a pull request:

* for python packages:
    * `make unittest` - Run the python unit tests.
    * `make lint` - Run the python linters.
* for golang services in the `legion/operator` directory:
    * `make test` - Run the golang unit tests.
    * `make lint` - Run the golang linters.
    * `make build-all` - Compile all golang legion services
* for typescript code in the `legion/jupyterlab-plugin` directory:
    * `yarn lint` - Run the typescript linter.
    * `jlpm run build` - Compile the jupyterlab plugin.

## Local Helm deploy

During development, you often have to change the helm chart, to test the changes you can use the following command
quickly: `make helm-install`.

Optionally, you can create the variables helm file and specify it using the `HELM_ADDITIONAL_PARAMS` Makefile option.
You always can download real variables file from a Terraform state. 
