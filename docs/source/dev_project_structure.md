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
* Jenkins - as optional model CI/CD server


# Repositories structure
## Legion
Project **Legion** locates in GitHub Repository [legion-platform/legion](https://github.com/legion-platform/legion) and contains of next items:

* Legion application - several Docker images:
  * EDI
  * EDGE
  * FluentD
  * Toolchain application
* [HELM packages](./gen_distros.md):
  * legion-core HELM chart
  * legion HELM chart
* Legion Python source codes
* [Operator](./cmp_operator.md)

### Legion's repository directory structure
* `containers` - all Legion components that are distributed as docker images. [Details](containers/README.md)
* `docs` - documentation that describes Legion platform, architecture, usage and etc.
* `examples` - examples of machine learning models that could be trained and deployed in Legion, examples base on public available models (such as sklearn digit classifier, MovieLens model, Logistic Regression classifier on Census Income Data) and some syntetic models. [Details](examples/README.md)
* `helms` - Legion Helm packages (distribution packages for Kubernetes).
* `legion` - source code of Legion python packages.
* `scripts` - utilitary scripts for CI/CD process.

## Infra-specific repositories
For deploying purposes there are platform-specific repositories that contains platform-specific deploying logic.

**Legion AWS** locates in GitHub Repository [legion-platform/legion-aws](https://github.com/legion-platform/legion-aws) and contains:
* Ansible playbooks
* Jenkinsfiles for Jenkins CI/CD jobs
* Infrastructure specific containers:
  * Ansible
  * Kube-elb-security - kubernetes controller that creates AWS security group rules for service ELB like ingress-nginx with granding access from all kubernetes nodes. It is useful if your services with Type LoadBalancer having firewall restrictions.
  * Kube-fluentd
  * Oauth2-proxy

## Additional integrations repositories
* [Airflow](https://github.com/legion-platform/legion-airflow)
* [Jenkins](https://github.com/legion-platform/legion-jenkins)
