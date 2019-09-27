# Project structure

## What is it inside Legion?
Core:
* Python 3.6, Golang – as main development languages
* Kubernetes – as runtime platform
* Docker – as containerization engine for runtime platform
* [FluentD](./cmp_feedback.md) – as logging aggregator for feedback loop
* [Operator](./cmp_operator.md) - as handler of Legion's custom resources
* [EDGE](./cmp_edge.md) – as model API traffic manager
* [EDI](./cmp_edi.md) – model manager
* [Toolchains](./tlch_about.md) - APIs for adding to ML Legion capabilities

Optional:
* Airflow – as optional ETL engine

# Repositories structure
## Legion
Project **Legion** locates in GitHub Repository [legion-platform/legion](https://github.com/legion-platform/legion) and contains of next items:

* Legion application - several Docker images:
  * EDI
  * FluentD
  * Toolchain application
* [HELM packages](./gen_distros.md):
  * legion-core HELM chart
  * legion HELM chart
* Legion Python source codes
* [Operator](./cmp_operator.md)

### Legion's repository directory structure
* `containers` - all Legion components that are distributed as docker images.
* `docs` - documentation that describes Legion platform, architecture, usage and etc.
* `helms` - Legion Helm packages (distribution packages for Kubernetes).
* `legion` - source code of Legion python packages.
* `scripts` - utility scripts for CI/CD process.

## Infra-specific repositories
For deploying purposes there are platform-specific repositories that contains platform-specific deploying logic.

**Legion Infrastructure** locates in GitHub Repository [legion-platform/legion-infrastructure](https://github.com/legion-platform/legion-infrastructure) and contains:
* Terraform modules
* Jenkins pipelines for Jenkins CI/CD jobs
* Infrastructure specific containers:
  * Terraform modules

## Additional integrations repositories

* [Legion Airflow plugin](https://github.com/legion-platform/legion-airflow-plugins)
* [Legion MLflow integration](https://github.com/legion-platform/legion-mlflow)
* [Legion examples](https://github.com/legion-platform/legion-examples)
* [Legion infrastructure](https://github.com/legion-platform/legion-infrastructure)
