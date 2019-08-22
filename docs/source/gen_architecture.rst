============================
Legion Platform Architecture
============================

Building, training and deploying
--------------------------------

Legion tries to unify process of training, building and deploying ML/AI models, splitting them to 3 main phases.

1. :term:`Model Training`
2. :term:`Model Packaging`
3. :term:`Model Deploying`

Legion provides an ability to develop applications/tools that can be used for these phases. These applications are:

1. :term:`Model Trainer`
2. :term:`Model Packager`
3. :term:`Model Deployer`

For cloud use case, these applications/tools have to be registered in Legion Platform using:

1. :term:`Toolchain Train Integration`
2. :term:`Toolchain Packaging Integration`

These registrations are required to have an ability to integrate training / packaging process with other subsystem Legion provides too (e.g. :term:`Model Training Metrics`, :term:`Model Training Tags`).


Storing of trained models
-------------------------

As an intermediate format for storing trained models Legion Platform declares :term:`Trained Model Binary Formats <Trained Model Binary Format>` for different languages.

Nowadays, Legion Platform declares:

1. :term:`General Python Prediction Interface`


Ready to use solutions
~~~~~~~~~~~~~~~~~~~~~~

There are ready for use :term:`Toolchain Train Integrations <Toolchain Train Integration>` and :term:`Toolchain Packaging Integration <Toolchain Packaging Integration>`:

1. :term:`MLflow Model Training Toolchain Integration`
2. :term:`Docker REST API Packaging Toolchain Integration`

But Legion Platform users are not limited to set of predefined :term:`Toolchain Train <Toolchain Train Integration>` and :term:`Toolchain Packaging <Toolchain Packaging Integration>` integrations and are free for installation of third-party integrations.

Legion subsystems
-----------------

Legion subsystems are:

1. :term:`EDI`
2. :term:`Operator`
3. :term:`Feedback aggregator`

These subsystems are optional, and can be deployed not just inside Legion Cloud, but even in other products.

Other integrations
------------------

For integration with Legion, there are libraries and plugins:

1. :term:`Python SDK Library`
2. :term:`Legion CLI`
3. :term:`Plugin for JupyterLab`
4. :term:`Plugin for Jenkins`
5. :term:`Plugin for Airflow`


Deploying of Legion Platform
----------------------------

Legion Platform can be installed locally or on Kubernetes cluster.