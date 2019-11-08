========
Glossary
========

.. glossary::

    VCS
        Version control system. A service that stores model source code for development
        and deployment procedures (e.g. a GitHub Repository).

    Trained Model Binary
        An archive containing a trained ML/AI model (inference code, model weights,
        etc). Legion defines a format for these binaries. See <ref_model_format.html>

    Trainer
        Application that uses model source code, :term:`Data Bindings <Data Binding>`,
        :term:`Connections <Connection>` and :term:`Training Hyperparameters` to produce
        a :term:`Trained Model Binary`.

    Data Binding
        Reference to remote data (e.g. files from S3) should be placed for a
        :term:`Train` process.

    Connection
        Credentials for an external system. For example: Docker Registry, cloud
        storage location, etc.

    Training Hyperparameters
        Parameter for Training process. For example, count of epochs in evolution algorithms.

    Train
        A containerized process that converts model source code,
        :term:`Data Bindings <Data Binding>`, :term:`Connections <Connection>`
        and :term:`Training Hyperparameters` to :term:`Trained Model Binary` using a :term:`Trainer`
        defined in a :term:`Trainer Extension`

    Trainer Extension
        A pluggable :term:`Train` implementation.

    Packager
        Containerized application that uses a :term:`Trained Model Binary` and :term:`Connections <Connection>`
        and converts them into a target Archive. Typically this is a Docker image with REST API.

    Package
        Containerized process which turns a :term:`Trained Model Binary` into a Docker image with REST API using a
        :term:`Packager Extension`.

    Packager Extension
        A pluggable :term:`Package` implementation.

    Deployer
        Containerized application that uses the results of a :term:`Package` process and
        :term:`Connections <Connection>` to deploy a packaged model on a Kubernetes cluster.

    Deploy
        Containerized process that `Deploys <Deploy>`results of a :term:`Package` operation to Kubernetes cluster with
        a REST web service.

    Trainer Metrics
         Metrics set by `Trainer` code during `Train` (e.g. accuracy of model). These metrics can be used for
         querying and comparing `Train` events.

    Trainer Tags
        Key/value value pairs that are set by `Trainer` code (e.g. type of algorithm). Can be used for querying and
        comparing `Train` runs.

    General Python Prediction Interface
        Format of storing models, written in a Python language

    MLflow Trainer
        Integration of MLflow library for training models, written in a Python. Details - :ref:`mod_dev_using_mlflow-section`

    REST API Packager
        Integration for packing trained models into Docker Image with served via REST API

    EDI
        API for managing Legion Platform resources for cloud deployed Platform

    Operator
        A Kubernetes Operator that manages Kubernetes resources (Pods, Services and etc.) for Legion
        :term:`Train`, :term:`Package`, and :term:`Deploy` instances.

    Prediction
        A deployed model output, given input parameters.

    Model prediction API
        API provided by deployed models to allow users to request predictions through a web service.

    Prediction Feedback
        Feedback versus the previous :term:`prediction`, e.g. prediction correctness.

    Model Feedback API
        An API for gathering :term:`Prediction Feedback <Prediction Feedback>`

    Feedback aggregator
        A service that provides a :term:`Model Feedback API` and gathers input and output
        :term:`prediction requests <Model prediction API>`

    Legion SDK
        An extensible Python client library for :term:`EDI`, written in Python language. Can be installed from PyPi.

    Legion CLI
        Command Line Interface for :term:`EDI`, written in Python. Can be installed from PyPi. It uses the :term:`Legion SDK`.

    Plugin for JupyterLab
        A legion-specific plugin that provides Legion Platform management controls in JupyterLab.

    Plugin for Jenkins
        A library for managing Legion Platform resources from Jenkins Pipelines.

    Plugin for Airflow
        A library that provides Hooks and Operators for managing Legion Platform resources from Airflow.

    Model Deployment Access Role Name
        Name of scope or role for accessing model deployments.

    JWT Token
        A JSON Web Token that allows users to query deployed models and to provide feedback. This token contains an
        encoded :term:`role name<Model Deployment Access Role Name>`.

    A/B testing
        Process of splitting predictions between multiple :term:`Model Deployments <Deploy>` in order to compare
        prediction metrics and :term:`Model Feedback<Prediction Feedback>` for models, which can vary by
        :term:`source code <VCS>`, :term:`dataset <Data Binding>` and/or
        :term:`training hyperparameters <Training Hyperparameters>`

    Legion distribution
        A collection of Docker Images, Python packages, or NPM packages, which are publicly available for
        installation as a composable Legion Platform.

    Legion Helm Chart
        A YAML definition for Helm that defines a Legion Platform deployed on a Kubernetes cluster.

    Legion's CRDs
        Objects that :term:`EDI` creates for actions that require computing resources
        to be stored. For example: :term:`connections <Connection>`, :term:`Trains <Train>`, etc).

        These objects are Kubernetes Custom Resources and are managed by :term:`operator`.
