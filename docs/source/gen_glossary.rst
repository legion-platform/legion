========
Glossary
========

.. glossary::

    VCS
        Version control system, place where model source codes are persisted for development and deploy procedures (e.g. Git Repository);

    Trained Model Binary
        Archive, that contains trained ML/AI model (inference code, model weights and etc.). Legion declares formats of these binaries;

    Trained Model Binary Format
        Format of storing trained ML/AI models.

    Model Trainer
        Application/tool, that takes source code of models (placed in VCS), :term:`Data Bindings <Data Binding>`, :term:`Connections <Connection>` and :term:`Training Hyperparameters` and produces :term:`Trained Model Binary`;

    Data Binding
        Declaration where remote data (e.g. files from S3) should be placed for :term:`Model Training` process;

    Connection
        Credentials for external systems, such as Docker Registry, cloud storages and etc.;

    Training Hyperparameters
        Parameter for training process, e.g. count of epochs in evolution algorithms;

    Model Training
        Process of converting model source codes (placed in VCS) with :term:`Data Bindings <Data Binding>`, :term:`Connections <Connection>` and :term:`Training Hyperparameters` to :term:`Trained Model Binary` using :term:`Model Trainer` application/tool declared in :term:`Toolchain Train Integration`;

    Toolchain Train Integration
        Pluggable mechanism of :term:`Model Training` processes;

    Model Packager
        Application/tool, that takes :term:`Trained Model Binary` and :term:`Connections <Connection>` and converts into target format,  such as Docker Image with REST API, Google Cloud function, AWS Lambda functions and etc.;

    Model Packaging
        Process of converting :term:`Trained Model Binary` into target format, such as Docker Image with REST API, Google Cloud function, AWS Lambda functions and etc. using :term:`Model Packager` application/tool declared in :term:`Toolchain Packaging Integration`;

    Toolchain Packaging Integration
        Pluggable mechanism of :term:`Model Packaging` processes;

    Model Deployer
        Application/tool, that takes results of (or references to) :term:`Model Packaging` and :term:`Connections <Connection>` to deploy this `artifacts` to target systems (such as Kubernetes cluster for Docker Image with REST API and etc.);

    Model Deploying
        Process of deploying results of (or references to) :term:`Model Packaging` to target systems (such as Kubernetes cluster for Docker Image with REST API and etc.) using :term:`Model Deployer` application/tool;

    Model Training Metrics
        Numeric metrics, that are being set by model training code during :term:`Model Training Process <Model Training>` (e.g. accuracy of model). Can be used for querying and comparing :term:`Model Trainings <Model Training>`;

    Model Training Tags
        Key/value (string/string) values that are being set by model training code during :term:`Model Training Process <Model Training>` (e.g. type of algorithm). Can be used for querying and comparing :term:`Model Trainings <Model Training>`;

    Model Prediction Metrics
        Metrics that provides information how fast is model, based on measuring process of handling :term:`predictions <Prediction>`;

    General Python Prediction Interface
        Format of storing models, written in a Python language;

    MLflow Model Training Toolchain Integration
        Integration of MLflow library for training models, written in a Python. Details - :ref:`mod_dev_using_mlflow-section`;

    Docker REST API Packaging Toolchain Integration
        Integration for packing trained models to Docker Image with REST API;

    EDI
        API for managing Legion Platform resources for cloud deployed Platform;

    Operator
        Kubernetes Operator that manages Kubernetes resources (Pods, Services and etc.) for providing resources for :term:`Model Trainings <Model Training>`, :term:`Model Packaging <Model Packaging>`, :term:`Model Deployments <Model Deploying>`;

    Prediction
        Query for deployed model, that contains input parameters (input vector) and returns prediction object. (e.g. prediction what is the number on the picture);

    Model prediction API
        API for predicting models. Depends on target deployment platform;

    Prediction Feedback
        Feedback for previous made :term:`prediction`. (e.g. was predicted number correct or not);

    Model Feedback API
        For for gathering :term:`Prediction Feedbacks <Prediction Feedback>`;

    Feedback aggregator
        Service, that provides :term:`Model Feedback API` and gathers input and output :term:`prediction traffic <Model prediction API>`;

    Python SDK Library
        SDK library for :term:`EDI`, written in Python language. Can be installed from PyPi;

    Legion CLI
        CLI interface for :term:`EDI`, written in Python language. Can be installed from PyPi. It uses :term:`Python SDK Library`;

    Plugin for JupyterLab
        Plugin for JupyterLab, that provides an ability to manage Legion Platform resources without leaving JupyterLab;

    Plugin for Jenkins
        Library for managing Legion Platform resources in Jenkins Pipelines;

    Plugin for Airflow
        Hooks and Operators for managing Legion Platform resources in Airflow;

    Model Deployment Access Role Name
        Name of scope/role for accessing model deployments;

    JWT Token
        JSON Web Token that allows users to query deployed models and to provide feedback (by querying feedback API). This token contains :term:`name of role <Model Deployment Access Role Name>`;

    A/B testing
        Process of splitting predictions between multiple :term:`Model Deployments <Model Deploying>` in order to compare :term:`prediction metrics <Model Prediction Metrics>`, :term:`feedbacks <Prediction Feedback>` for models, trained with different :term:`source codes <VCS>`, :term:`train datasets <Data Binding>` and :term:`training hyperparameters <Training Hyperparameters>`;

    Legion distribution
        Collection of Docker Images, Python packages, NPM packages and etc., which are public available for installation;

    Legion HELM Chart
        Package, that can be install on Kubernetes cluster. It uses :term:`Legion's Docker Images <Legion distribution>`;

    Legion's CRDs
        Objects, that :term:`EDI` creates for actions that require computing resources or to be stored (:term:`connections <Connection>`, :term:`model trainings <Model Training>` and etc.).

        These objects are Kubernetes Custom Resources and are being handled by :term:`opertor`;


