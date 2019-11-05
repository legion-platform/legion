=====
Legion distributions
=====

:term:`Legion distributions<Legion distribution>` are provided via :term:`HELM Charts <Legion HELM Chart>`, docker images, Python and NPM packages.

HELM charts
----
Legion distributes :term:`HELM Chart <Legion HELM Chart>` named **legion**, that contains all Legion's components, such as **EDI**, **CR Operator**, etc.

HELM chart locations
~~~~~

- Release and pre-release :term:`HELM Charts <Legion HELM Chart>` are in `github<https://github.com/legion-platform/legion-helm-charts>`_.


Docker Images
------

.. csv-table::
   :header: "Name", "Image name", "Description"
   :widths: 20, 30, 40

   "Pipeline agent", "`legion-pipeline-agent`", "CI/CD pipeline component (not used by Legion cluster)"
   "EDI", "`k8s-edi`", "Management API"
   "Fluentd", "`k8s-fluentd`", "Log aggregator"
   "Feedback aggregator", "`k8s-feedback-aggregator`", "Feedback aggregator, traffic capture"
   "Kubernetes Operator", "`k8s-operator`", "CustomResource Operator"
   "Model builder", "`k8s-model-builder`", "Training process sidecar"


.. todo::

   Update model builder & training images due to changes in packaging & training


Docker images locations
~~~~~

- Release versions of images are on Docker Hub in `legionplatform <https://hub.docker.com/u/legionplatform>`_ organization. Example image name is `legionplatform/k8s-edi`.

- Pre-release versions of images are on Docker Hub in `legionplatformtest <https://hub.docker.com/u/legionplatformtest>`_ organization. Example image name is `legionplatformtest/k8s-edi`.

Python packages
-----

.. csv-table::
   :header: "Name", "Description"
   :widths: 20, 40

   "legion-cli", "Legion CLI tool"
   "jupyter_legion", "Back-end for JupyterLab plugin"
   "legion-robot", "Utility functions for E2E tests"
   "legion-sdk", "SDK library for Legion API (client)"


Python packages locations
~~~~~

- Release versions on Python packages are on PyPi in project `legion <https://pypi.org/project/legion/>`_.

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


.. todo::

   Add NPM packages locations
