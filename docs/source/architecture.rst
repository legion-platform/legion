============================
Architecture
============================

Subsystems
--------------------------------

Legion subsystems are:

1. :term:`EDI`
2. :term:`Operator`
3. :term:`Feedback aggregator`

External integrations
--------------------------------

These tools and libraries are Legion clients:

1. :term:`Legion SDK`
2. :term:`Legion CLI`
3. :term:`Plugin for JupyterLab`
4. :term:`Plugin for Jenkins`
5. :term:`Plugin for Airflow`

Deployment
--------------------------------

The Legion Platform can be installed locally or on a Kubernetes cluster.

Technologies
--------------------------------

- **Python Language** - build toolchains, Packagers and Deployers.

- **Go Language** - Legion Platform orchestration (using `dep <https://golang.github.io/dep/>`_).

- **Kubernetes** – Any Cloud support

- **HELM** - Legion as K8s App Deployment

- **FluentD** – log aggregation for feedback loop and cluster logging
