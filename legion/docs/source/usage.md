# Usage
legion contains of many docker containers, including next:
* [jupyter](jupyter.md) - with Jupyter notebook
* [legion](legion.md) - with default model HTTP handler
* [graphite](grafana_and_graphite.md) - for saving model timings
* [grafana](grafana_and_graphite.md) - with GUI for model timings
* [jenkins](jenkins.md) - for running model tests
* [edge](edge.md) - with Nginx server for handling all requests


## How to run
* Activate docker-machine
```bash
eval "$(docker-machine env default)"
```
* Run operational stack
```bash
./stack -f docker-compose.dev.yml up
```

## How to build models
For build models you need to call `legion.io.export` with correct arguments.
You can do this locally or in Jupyter container.

For access Jupyter container open [parallels/jupyter](http://parallels/jupyter).

After building model should be stored in local directory with *.model* extension.

*.model* files should be build in model images (*Docker images*) 
using `legion build` command.

## How to deploy models
You can get information about existing model images and model instances (deployed models)
using command `legion deploy`. 

For deploying new model you need to call `legion deploy`.
For un deploying models you need to call `legion undeploy`.

## How to test
You can run static analyzers in legion-root/legion folder
```bash
tox
pylint
```
For unit and system testing you can use nosetests
```bash
nosetests --cover-package legion
```

## How to work with deployed models
After deploying models starts HTTP server and handles REST API requests.
REST API described in next document: [Model REST API](model_rest_api.md)