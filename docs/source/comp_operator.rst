========
Operator
========

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Technologies used", "GoLang"
    "Distribution representation", "Docker Image"
    "Source code location", "`legion/legion/operator <https://github.com/legion-platform/legion/tree/develop/legion/operator>`_"
    "Can be used w/o Legion Platform?", "Yes"
    "Does it connect to another services?", "Yes (Kubernetes API)"
    "Can be deployed locally?", "If local Kubernetes cluster is present"
    "Does it provide any interface?", "No"


Operator is a mandatory component in Legion platform for cluster installation. It monitors :term:`Legion's CRDs` for changes and
manages appropriate Kubernetes resources (Kubernetes Secrets, Pods, Services and etc.).

Operator is written using Golang and kubebuilder framework.

How does operator make training?
----------------------------------
For each [training CRD](./ref_crds.md) operator creates appropriate configured Kubernetes Pod that consists of:

* Model's container, created from specified (or default for selected toolchain) image.
  This container is launched with infinity sleep command and is controlled from builder's container.
* Builder's container, created from `k8s-model-builder` docker image. Details about builder are [below](#what-is-builder).
* VolumeMount to [Git Repository credentials](./ref_crds.md).

Details about training CustomResource are provided in [another chapter](./ref_crds.md).

What is builder?
----------------------------------
Builder is responsible for:

1. Checking out sources from Git repository.
2. Running start command in model's container and awaiting results.
3. Building and pushing model using `legionctl build command` inside itself.

Builder's image contains `legionctl` CLI tool and `builder` CLI tool that is started on startup.

How does operator manage deployment?
----------------------------------
For each [deployment CRD](./ref_crds.md) operator creates:

* Deployment and Pod - with target model image.
* Service - for routing traffic.


How to reach EDI in target cluster
----------------------------------

Because of the fact that :term:`operator` does not provide any interfaces for connecting,
you can not reach it directly.

Implementation details
----------------------------------

:term:`Operator` is a Kubernetes Operator, written using GoLang (with usage of Kubernetes's official Go packages).