======
About Legion Platform
======

.. figure:: ../images/legion-logo-h.png
   :scale: 50 %
   :alt: Legion Platform logo

The Legion is an open source project dedicated to simplify automation of AI/ML products life cycle for small and large-scale enterprise systems.

## Overview

- **Modular Architecture**
  - Separate components for different AI product life cycle phases: training, packaging and deployment
  - RESTful APIs and SDKs for all components to build extensions and plugins for external systems
  - Command line interface to interact with system components
  - Plugins for IDEs, Workflow Engines, CICD Engines
- **Multi Cloud**
  - Core system components are deployed in K8S
  - Deployment automation for major clouds: AWS, Azure, GCP
- **Security**
  - Single sign-on (SSO) for all system components
  - Credentials and security keys manager
- **Multi AI/ML Toolchain**
  - All major ML Toolchains (Scikit-learn, Keras, Tensorflow, PyTorch, H2O and others) are supported
  - Integrated with MLFlow open source project

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
