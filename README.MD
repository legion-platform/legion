![LegionLogo](docs/images/legion-logo-h.png)

Legion is a Machine Learning Toolkit that can be used for ML models training both locally and on Kubernetes cluster.

## Overview

Legion originated around the idea of creating a flexible unified platform to run AI Learning models in production.

Legion’s goal is to provide a comprehensible way for deployment of ML models both in research and production with minimum code rewrite and maximum traceability.

Legion craves to streamline the process of delivering ML models into production offering out-of-the- box CI/CD environment with integrated model quality control, scheduled retraining and automated testing alongside with real-time performance evaluation.

Legion is open, comprehensible, flexible and scalable platform to suit a wide range of the users’ needs.

* **Open** - Legion is an open source project with its friendly community on [GitHub](https://github.com/legion-platform/legion).
* **Comprehensible** - you can install Legion with minimum effort and track performance of ML models internals and compare their predictions.
* **Flexible** - well-versed user can manage and control ML model building and training, at the same time, newcomers will find it easy to use.
* **Scalable** - you can use existing and new models with the added architecture and feature sets.

The platform was designed in such a way that it contains the capabilities needed for model development purposes using supported [toolchains](docs/source/toolchains.md) (Python) as well as for the platform deployment (onto Kubernetes Cluster).

It also includes the components that are deployed on the cluster (**Grafana**, **Prometheus**) and the ones that are required for that deployment (**Terraform**, **Helm**) or building Legion's components from source code (**Jenkins files**).

### Legion provides:

* Effortless out-of-the-box CI/CD process, including integrated model quality control with automated retraining and regression testing.
* Cloud-agnostic AI toolchains integrated with the most popular Sklearn, Tensorflow, Spark, R.
* Integrated feedback loop for the input and output capturing, A/B testing and traffic management support.


## Documentation
**HERE WILL BE A COPY OF DOC'S INDEX.RST**

## Changelog
Please find it here [CHANGELOG](CHANGELOG.md)

## Backlog and Kanban Board
* [Backlog](https://github.com/legion-platform/legion/issues)
* [Kanban Board](https://github.com/orgs/legion-platform/projects/1)

## Contact Us
If you are interested in contribution to Legion feel free to create a pull request or create an issue report.
If you interested in hearing more about Legion implementation, existing case studies, questions or concerns  feel free to contact us at [Legion discussion group](https://groups.google.com/forum/#!forum/legion-platform/new).
