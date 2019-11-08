========
Operator
========

**Operator** monitors Legion-provided Kubernetes (K8s)
`Custom Resources <https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/>`_.
This gives Operator the ability to manage Legion entities using K8s infrastructure (Secrets, Pods, Services, etc).
The K8s entities that belong to Legion are referred to as :term:`Legion's CRDs`.

Operator is a mandatory component in Legion clusters.

Legion Model Pods
-----------------
For each model, operator creates a K8s pod containing:
* a Builder container, created from `k8s-model-builder` image
* a Model container, created from a toolchain image. The toolchain is specified as an argument to EDI
* a VolumeMount for source code, using a `Connection` (usually to Git)
* (optional) other resources (e.g. GCS or S3 buckets)

Train Process
-------------
1. Check out source code
2. Execute Train, produce .zip file

Build Process
-------------
3. Execute Build, produce Docker image
4. Push image to Docker repository

Deploy Process
----------------------------------
5. Create K8s pod
6. Deploy image to pod
7. Create service to route traffic

Connecting to Operator
----------------------------------

Operator does not ship a connection interface.

Implementation details
----------------------------------

:term:`Operator` is a Kubernetes Operator, written using Kubernetes Go packages.

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
