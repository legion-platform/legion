=====
Legion distributions
=====

Legion provides pre-built :term:`HELM Chart <Legion HELM Chart>`, Docker Images, Python packages and NPM packages as a :term:`Legion distribution`.

HELM charts
----
Legion distributes :term:`HELM Chart <Legion HELM Chart>` named **legion**, that contains all Legion's components, such as **EDI**, **CR Operator** and etc.

HELM chart locations
~~~~~

- Release and pre-release versions of :term:`HELM Charts <Legion HELM Chart>` are in special Git Repository named `legion-platform/legion-helm-charts <https://github.com/legion-platform/legion-helm-charts>`_.

- Source codes of Legion's charts are in `/helms <https://github.com/legion-platform/legion/tree/develop/helms>`_ folder of `Legion's repository <https://github.com/legion-platform/legion>`_. There up-to-date HELM charts for each branch can be found.

- Development versions of :term:`HELM Charts <Legion HELM Chart>` are on `development server <https://nexus.cc.epm.kharlamov.biz/repository/helm-main/>`_ that is not accessible from Internet, but accessible from CI/CD server.

Docker Images
------

.. csv-table::
   :header: "Name", "Image name", "Description"
   :widths: 20, 30, 40

   "Pipeline agent", "`legion-pipeline-agent`", "Is used in CI/CD pipeline, contains all build, test and deploy requirements. (Is not used as a cluster component)"
   "EDI", "`k8s-edi`", "Cluster management REST API"
   "Fluentd", "`k8s-fluentd`", "Logging aggregator"
   "Feedback aggregator", "`k8s-feedback-aggregator`", "Feedback aggregator & traffic capturer"
   "Kubernetes Operator", "`k8s-operator`", "Kubernetes CustomResource operator"
   "Model builder", "`k8s-model-builder`", "Sidecar for training process"


.. todo::

   Update model builder & training images due to changes in packaging & training


Docker images locations
~~~~~

- Release versions of images are on Docker Hub in `legionplatform <https://hub.docker.com/u/legionplatform>`_ organization. Example image name is `legionplatform/k8s-edi`.

- Pre-release versions of images are on Docker Hub in `legionplatformtest <https://hub.docker.com/u/legionplatformtest>`_ organization. Example image name is `legionplatformtest/k8s-edi`.

- Development versions of images are on `development server <nexus.cc.epm.kharlamov.biz:443/legion>`_ that is not accessible from Internet, but accessible from CI/CD server. Example image name is `nexus-local.cc.epm.kharlamov.biz:443/legion/k8s-edi`.

Python packages
-----
Legion provides next Python packages:

.. csv-table::
   :header: "Name", "Description"
   :widths: 20, 40

   "legion-cli", "CLI for Legion API"
   "jupyter_legion", "Back-end for JupyterLab plugin"
   "legion-robot", "Util functions for E2E tests"
   "legion-sdk", "SDK library for Legion API (client)"


Python packages locations
~~~~~

- Release versions on Python packages are on PyPi in project `legion <https://pypi.org/project/legion/>`_.

- Pre-release and development versions of Python package are on `development server <https://nexus.cc.epm.kharlamov.biz/repository/pypi-proxy/>`_ that is not accessible from Internet, but accessible from CI/CD server.

.. todo::

   Update Python package locations


NPM packages
-----

.. csv-table::
   :header: "Name", "Description"
   :widths: 20, 40

   "jupyter_legion", "JupyterLab plugin for Legion (requires python back-end)"

NPM packages locations
~~~~~~

- Release versions on Python packages are on npm in project legion.

- Pre-release and development versions of Python package are on `development server <https://nexus.cc.epm.kharlamov.biz/repository/>`_ that is not accessible from Internet, but accessible from CI/CD server.


.. todo::

   Add NPM packages locations
