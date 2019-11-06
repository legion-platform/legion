=========================================
Pre-requirements for on-cluster deploying
=========================================

Legion Platform can be deployed on top of Kuberenetes cluster using HELM tool.

Requirements
------------

Kubernetes cluster
~~~~~~~~~~~~~~~~~~
Legion platform could be deployed on bare-metal / PaaS Kubernetes cluster.

.. important::

    Kubernetes version required: at least 1.11.


Installed HELM tool
~~~~~~~~~~~~~~~~~~~

Entire Legion platform is distributed as a HELM Chart and Docker images (details in appropriate chapter) and you have to use `HELM tool <https://helm.sh>`_ to deploy legion on your cluster.

Currently Legion supports HELM (client and server) version **2** (at least **2.10** minor version).


Deploying
---------

To deploy Legion on Kubernetes cluster, you have to:

- Authorize on cluster

- Ensure that HELM is Installed

- Create configuration file for Legion HELM chart, e.g. ``values.yaml`` using according chapter or use predefined example.

- Install Legion HELM chart using configuration file

.. code-block:: bash

    helm install legion -f values.yaml --name legion --repo https://github.com/legion-platform/legion-helm-charts


That's all, starting this moment, you can:

- Manage model trainings

- Manage model packaging

- Manage model deployments

- Ask deployed models for prediction

- Make A/B tests for model deployments

- Analyze train and performance metrics

- Send feedback for previously made predictions
