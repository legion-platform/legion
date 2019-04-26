# Operator

Operator is a main (and mandatory) component in Legion platform. It monitors [Legion's CRDs](./ref_crds.md) for changes and
 manages appropriate Kubernetes resources (e.g. Secrets and Pods).

Operator is written using Golang and kubebuilder framework.

## How operator makes training?
For each [training CRD](./ref_crds.md) operator creates appropriate configured Kubernetes Pod that consists of:
* Model's container, created from specified (or default for selected toolchain) image.
  This container is launched with infinity sleep command and is controlled from builder's container.
* Builder's container, created from `k8s-model-builder` docker image. Details about builder are [below](#what-is-builder).
* VolumeMount to [Git Repository credentials](./ref_crds.md).

Details about training CustomResource are provided in [another chapter](./ref_crds.md).

### What is builder?
Builder is responsible for:
1. Checking out sources from Git repository.
2. Running start command in model's container and awaiting results.
3. Building and pushing model using `legionctl build command` inside itself.

Builder's image contains `legionctl` CLI tool and `builder` CLI tool that is started on startup.

## How operator manages deployment?
For each [deployment CRD](./ref_crds.md) operator creates:
* Deployment and Pod - with target model image.
* Service - for routing traffic.
