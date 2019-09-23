![LegionLogo](docs/images/legion-logo-h.png)

The Legion is an open source project dedicated to simplify automation of AI/ML products life cycle for small and large-scale enterprise systems.

## Overview

* **Modular Architecture**
  * Separate components for different AI product life cycle phases: training, packaging and deployment
  * RESTful APIs and SDKs for all components to build extensions and plugins for external systems
  * Command line interface to interact with system components
  * Plugins for IDEs, Workflow Engines, CICD Engines
* **Multi Cloud**
  * Core system components are deployed in K8S
  * Deployment automation for major clouds: AWS, Azure, GCP
* **Security**
  * Single sign-on (SSO) for all system components
  * Credentials and security keys manager
* **Multi AI/ML Toolchain**
  * All major ML Toolchains (Scikit-learn, Keras, Tensorflow, PyTorch, H2O and others) are supported
  * Integrated with MLFlow open source project

## Documentation

[Documentation sources](/docs/source)

## Changelog
Please find it here [CHANGELOG](CHANGELOG.md)

## Backlog and Kanban Board
* [Backlog](https://github.com/legion-platform/legion/issues)
* [Kanban Board](https://github.com/orgs/legion-platform/projects/1)

## Contribution
If you are interested in contribution to project feel free to create an issue in [backlog](https://github.com/legion-platform/legion/issues), create a pull request.
