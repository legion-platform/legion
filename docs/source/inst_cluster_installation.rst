.. _installation-prereqs:
=========================================
Prerequisites
=========================================

Kubernetes
--------

Legion Platform runs on Kubernetes.

.. important::

    Kubernetes version must be at least 1.11

Legion is built and tested against `EKS <https://aws.amazon.com/eks/>`_, `AKS <https://azure.microsoft.com/en-us/services/kubernetes-service/>`_, and `GKE <https://cloud.google.com/kubernetes-engine/>`_.

Installing on a self-managed Kubernetes cluster is straight-forward.

Helm
--------

The Legion Platform is distributed as a `Helm <https://helm.sh>`_ `chart <https://helm.sh/docs/developing_charts/>`_.

.. important::
    Legion supports Helm version **2** (minor version >= **2.10**)

=========================================
Legion
=========================================

To deploy Legion on Kubernetes cluster, you have to:

- Authorize against Kubernetes cluster (:ref:`instructions <https://kubernetes.io/docs/reference/access-authn-authz/authorization/>`_)

- Copy and update a ``values.yaml`` file. (`example file <configuration-values-yaml>`)

- Install

.. code-block:: bash

    helm install legion -f values.yaml --name legion --repo https://github.com/legion-platform/legion-helm-charts

Success!

From this point on you can:

- Automate model Train, Package, and Deploy
- Query deployed models for predictions
- Do model A/B testing
- Analyze Train and model performance metrics
- Send feedback from previous predictions

=========================================
Legion CLI
=========================================

.. _legion_cli-install:

HOWTO INSTALL :term:`Legion CLI`

=========================================
Jupyter Plugin
=========================================

.. _jupyter_plugin-install:

HOWTO INSTALL :term:`Plugin for JupyterLab`