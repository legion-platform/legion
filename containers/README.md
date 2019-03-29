## Directory information

This directory contains all Legion components that are distributed as docker images.

### Components
* **EDGE** is a model API Gateway based on OpenResty. [Details in documentation](../docs/source/edge.md)
* **EDI** is a service which allows managing model inside Kubernetes. [Details in documentation](../docs/source/edi.md)
* **FluentD** is a `fluentd-elasticsearch` image with S3 plugin. [Details in documentation](../docs/source/feedback-loop.md)
* **Jenkins** is a modification of Jenkins CI/CD system with additional Legion plugins. Uses for model building. _Will be removed._
* **Pipeline-agent** is a docker image for CI/CD process. Inside this Docker image almost all build stages are being executed.
* **Toolchains** contains implementation of toolchains (model extension API) for each supported platform. [Details in documentation](../docs/source/toolchains.md)


## How to build
To build these images you may use Makefile from the root folder of repository. (e.g. `make docker-pipeline`).

If you want to build these images without Make, you have to run `docker build` command from the root folder of repository. (e.g. `docker build -t legionplatform/k8s-edi:latest -f containers/edi/Dockerfile .`)