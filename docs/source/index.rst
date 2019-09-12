======
About Legion Platform
======

.. figure:: ../images/legion-logo-h.png
   :scale: 50 %
   :alt: Legion Platform logo

   Legion is a Machine Learning Toolkit that can be used for ML models
   training both locally and on Kubernetes cluster.

Legion is a Machine Learning Toolkit that can be used for ML models :term:`training <Model Training>` (both locally and on Kubernetes cluster), :term:`packing <Model Packaging>` (to supported target formats, such as Docker image with REST api) and :term:`deploying <Model Deploying>` to target platform.

Legion originated around the idea of creating a flexible unified platform to run AI Learning models in production.

Legion’s goal is to provide a comprehensible way for training and deployment of ML models both in research and production with minimum code rewrite and maximum traceability.

Legion craves to streamline the process of delivering ML models into production offering out-of-the- box CI/CD environment with integrated model quality control, scheduled retraining and automated testing alongside with real-time performance evaluation.

Legion is open, comprehensible, flexible and scalable platform to suit a wide range of the users’ needs.

- **Open** - Legion is an open source project with its friendly community on `GitHub <https://github.com/legion-platform/legion>`_.

- **Comprehensible** - you can install Legion with minimum effort and track performance of ML models internals and compare their :term:`predictions <Prediction>`.

- **Flexible** - well-versed user can manage and control ML model :term:`training <Model Training>` and :term:`packing <Model Packaging>`, at the same time, newcomers will find it easy to use.

- **Scalable** - you can use existing and new models with the added architecture and feature sets, provide your own :term:`trainers <Model Trainer>`, :term:`packagers <Model Packager>` and :term:`deployers <Model Deployer>`.

The platform was designed in such a way that it contains the capabilities needed for model development purposes using supported :term:`train toolchains <Toolchain Train Integration>` (e.g. :term:`integration with MLflow <MLflow Model Training Toolchain Integration>`, :term:`packing integrations <Toolchain Packaging Integration>` (such as packing to :term:`Docker Image with REST API <Docker REST API Packaging Toolchain Integration>`) as well as for the :term:`platform deployment <Model Deploying>` (onto Kubernetes Cluster).

It also includes the components that are deployed on the cluster (**Monitoring**, **Dashboards**) and the ones that are required for that deployment (**Terraform**, **Helm**) or building Legion's components from source code (**Jenkins files**).


What does Legion provide?
-------

- Effortless out-of-the-box CI/CD process, including integrated model quality control with automated testing;

- Common environment for :term:`training of ML models <Model Training>`;

- Configurable, secure (via :term:`JWT tokens <JWT Token>`) model deployment with :term:`A/B testing`;

- :term:`Performance measurement <Model Prediction Metrics>` and performance tests for models;

- :term:`Library-agnostic format <Trained Model Binary Format>` for persisting trained models on a disk;

- Cloud-agnostic AI/ML :term:`training toolchains <Toolchain Train Integration>` and :term:`packing toolchains <Toolchain Packaging Integration>`;

- Ability to :term:`deploy models <Model Deploying>` to different target systems;

- Integrated :term:`feedback loop <Feedback aggregator>` and :term:`the input and output capturing <Feedback aggregator>`;

- :term:`Model management REST API <EDI>` and :term:`Python SDK client <Python SDK Library>` for them;

- Security authentication that could be connected to LDAP, SAML and OAuth providers;

- Integration with ETL processing engines;

- Acceleration of time-to-market period for ML models creation.


======
Documentation
======

.. toctree::
   :maxdepth: 2
   :caption: General Overview:

   gen_glossary
   gen_architecture
   gen_used_technologies
   gen_distros
   gen_security

.. toctree::
   :maxdepth: 2
   :caption: Installation:

   inst_cluster_installation
   inst_kubernetes_integrations

.. toctree::
   :maxdepth: 2
   :caption: Model development

   installation
   configuration
   usage
   system_architecture
   model_rest_api
   local_run
   legionctl
   model_artifacts_format
   mod_dev_using_mlflow

.. toctree::
   :maxdepth: 2
   :caption: Model Training

    mod_train_general
    mod_train_trainer_protocol

.. toctree::
   :maxdepth: 2
   :caption: Model Binary formats

   mod_binf_general
   mod_binf_gppi

.. toctree::
   :maxdepth: 1
   :caption: Using of deployed models
   gs_feedback_loop


.. toctree::
   :maxdepth: 1
   :caption: Components details:

   comp_edi
   comp_operator
   grafana_and_graphite
   jenkins
   rbac

.. toctree::
   :maxdepth: 1
   :caption: Development:

   dev_general
   dev_project_structure
   dev_building
   dev_testing

.. toctree::
   :maxdepth: 1
   :caption: Custom integrations:

   int_metrics
   int_airflow
   int_jenkins

.. toctree::
   :maxdepth: 1
   :caption: Toolchains:

   tlch_about
   tlch_python

.. toctree::
   :maxdepth: 1
   :caption: References:

   ref_configuration
   ref_model_rest_api
   ref_feedback_loop_protocol
   ref_network_connectivity
   ref_legion_helm_values_examples


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
