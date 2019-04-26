# Overview

Legion is a Machine Learning Toolkit that can be used for ML models training both locally and on Kubernetes cluster.

Legion originated around the idea of creating a flexible unified platform to run AI Learning models in production.

Legion’s goal is to provide a comprehensible way for deployment of ML models both in research and production with minimum code rewrite and maximum traceability.

Legion craves to streamline the process of delivering ML models into production offering out-of-the- box CI/CD environment with integrated model quality control, scheduled retraining and automated testing alongside with real-time performance evaluation.

Legion is open, comprehensible, flexible and scalable platform to suit a wide range of the users’ needs.

* **Open** - Legion is an open source project with its friendly community on [GitHub](https://github.com/legion-platform/legion).
* **Comprehensible** - you can install Legion with minimum effort and track performance of ML models internals and compare their predictions.
* **Flexible** - well-versed user can manage and control ML model building and training, at the same time, newcomers will find it easy to use.
* **Scalable** - you can use existing and new models with the added architecture and feature sets.

The platform was designed in such a way that it contains the capabilities needed for model development purposes using supported [toolchains](./tlch_about.md) (such as [Python](./tlch_python.md)) as well as for the platform deployment (onto Kubernetes Cluster).

It also includes the components that are deployed on the cluster and the ones that are required for that deployment (**Ansible**, **Helm**) or building Legion's components from source code (**Jenkins files**).

## What does Legion provide?

* Effortless out-of-the-box CI/CD process, including integrated model quality control with automated testing;
* Common environment for training of ML models
* Configurable, secure (via JWT) model deployment with A/B testing.
* Performance measurement and performance tests for models;
* Cloud-agnostic AI toolchains integrated with the most popular Sklearn package and we are about to add some more on the list.
* Integrated feedback loop for the input and output capturing;
* Model management REST API;
* Security authentication that could be connected to LDAP, SAML and OAuth providers;
* ETL processing engine.
* Acceleration of time-to-market period for ML models creation
