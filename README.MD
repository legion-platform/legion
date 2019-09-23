![LegionLogo](docs/images/legion-logo-h.png)

The Legion is an open source project dedicated to simplify automation of AI/ML products life cycle for small and large-scale enterprise systems.

## Overview

* **Modular Architecture**
  * Separate components for different AI product life cycle phases: training, packaging and deployment
  * RESTful APIs and SDKs for all components to build extensions and plugins for external systems
  * Command line interface to interact with system components
  * Plugins for IDEs, Workflow Engines, CICD Engines
  * ML experiments tracking component 
  * Logging, monitoring and alerting components
* **Multicloud**
  * Core system components deployment in K8S with Helm Charts
  * Deployment automation for major clouds: AWS, Azure, GCP with Terraform 
* **Security**
  * Single sign-on (SSO) with OAuth2 or SAML2
  * System API endpoints secured with JWT tokens
  * Credentials manager for connectors to external systems 
* **Multiple AI/ML Toolchains**
  * All major ML toolchains Scikit-learn, Keras, Tensorflow, PyTorch, H2O and others are supported
  * Integrated with MLFlow open source project

## Documentation

[Documentation sources](/docs/source)

## Changelog
Please find it here [CHANGELOG](CHANGELOG.md)

## Backlog and Kanban Board
* [Backlog](https://github.com/legion-platform/legion/issues)
* [Kanban Board](https://github.com/orgs/legion-platform/projects/1)

## License
[Apache 2.0](LICENSE)

## Contribution
If you are interested in contribution to project feel free to create an issue in [backlog](https://github.com/legion-platform/legion/issues), create a pull request.
