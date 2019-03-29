# Project structure

## What is it inside Legion?
Core:
* Python 3.6 – as main development language
* Ansible – as tool for implementing infra-as-a-code
* Kubernetes – as runtime platform
* Docker – as containerization engine for runtime platform
* Grafana – as metrics dashboard
* Prometheus – as storage for cluster metrics
* FluentD – as logging aggregator for cluster logs and feedback loop
* EDGE – as model API traffic manager
* EDI – model manager
* Toolchains - APIs for adding to ML Legion capabilities

Optional:
* Airflow – as optional ETL engine


# Repositories structure
## Legion
Project **Legion** locates in GitHub Repository [legion-platform/legion](https://github.com/legion-platform/legion) and contains of next items:

* Legion application - several Docker images:
  * EDI
  * EDGE
  * FluentD
  * Toolchain application
* HELM packages:
  * legion-core HELM chart
  * legion HELM chart
* Legion Python source codes
* Legion Operator (not released yet)

## Legion for AWS
For deploying purposes there are platform-specific repositories that contains platform-specific deploying logic.

**Legion AWS** locates in GitHub Repository [legion-platform/legion-aws](https://github.com/legion-platform/legion-aws) and contains:
* Ansible playbooks
* Jenkinsfiles for Jenkins CI/CD jobs
* Infrastructure specific containers:
  * Ansible
  * Kube-elb-security - kubernetes controller that creates AWS security group rules for service ELB like ingress-nginx with granding access from all kubernetes nodes. It is useful if your services with Type LoadBalancer having firewall restrictions.
  * Kube-fluentd
  * Oauth2-proxy

## Legion Airflow


## Legion CI

_UNDER CONSIDERATION_