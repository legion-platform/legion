.. _installation-prereqs:
=============
Prerequisites
=============

Kubernetes
--------

Legion Platform runs on Kubernetes.

.. important::

    Kubernetes version must be at least 1.11

Legion is built and tested against `EKS <https://aws.amazon.com/eks/>`_, `AKS <https://azure.microsoft.com/en-us/services/kubernetes-service/>`_, and `GKE <https://cloud.google.com/kubernetes-engine/>`_.

Installing on a self-managed Kubernetes cluster is straight-forward.

.. _installation-helm:
Helm
--------

The Legion Platform is distributed as a `Helm <https://helm.sh>`_ `chart <https://helm.sh/docs/developing_charts/>`_.

.. important::
    Legion supports Helm version **2** (minor version >= **2.10**)

=========================================
Legion
=========================================

To deploy Legion on a Kubernetes cluster, you have to:

- Authorize against Kubernetes cluster. Instructions for: `EKS <https://docs.aws.amazon.com/cli/latest/reference/eks/get-token.html>`_, `GKE <https://cloud.google.com/sdk/gcloud/reference/container/clusters/get-credentials>`_, `AKS <https://docs.microsoft.com/en-us/cli/azure/aks?view=azure-cli-latest#az-aks-get-credentials>`_, `self-managed K8s <https://kubernetes.io/docs/reference/access-authn-authz/authorization/>`_

- Copy and update a ``values.yaml`` file: :ref:`values-yaml`

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

.. todo:
    implement next section

HOWTO INSTALL :term:`Legion CLI`

=========================================
Jupyter Plugin
=========================================

.. _jupyter_plugin-install:

.. todo:
    implement next section

HOWTO INSTALL :term:`Plugin for JupyterLab`