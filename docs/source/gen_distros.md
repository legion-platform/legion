# Legion distributions

Legion provides pre-built HELM Charts, Docker images and Python packages available for instant deploy.

## HELM charts
Legion distributes as 2 HELM Charts:
* `legion-crds` - this chart contains Legion's Kubernetes Custom Resource Definitions.
   **NOTE: This chart should be installed first.**
* `legion` - this chart contains all Legion's components, such as [EDI](./cmp_edi.md), [EDGE](./cmp_edge.md), [CR Operator](./cmp_operator.md).

### HELM charts locations
* Release and pre-release versions of HELM charts are in special Git Repository named [legion-platform/legion-helm-charts](https://github.com/legion-platform/legion-helm-charts).
* Source codes of Legion's charts are in [/helms](https://github.com/legion-platform/legion/tree/develop/helms) folder of [Legion's repository](https://github.com/legion-platform/legion). There up-to-date HELM charts for each branch can be found.
* Development versions of HELM charts are on [development server](https://nexus.cc.epm.kharlamov.biz/repository/helm-main/) that is not accessible from Internet, but accessible from CI/CD server.

## Docker images
Legion chart uses Legion's Docker images:

| Image name                | Dockerfile                              | Sources                                          | Description                                                                 | Documentation        |
|-------------------------|-----------------------------------------|--------------------------------------------------|-----------------------------------------------------------------------------|----------------------|
| `legion-pipeline-agent`   | containers/pipeline-agent/Dockerfile | entire repository | Is used in CI/CD pipeline, contains all build, test and deploy requirements. (Is not used as cluster component) | [Building Legion](./dev_building.md) |
| `k8s-edge`                | containers/edge/Dockerfile | legion/sdk, legion/services | Traffic router | [EDGE](./cmp_edge.md) |
| `k8s-edi`                 | containers/edi/Dockerfile | legion/sdk, legion/services | Model deployment and training manager | [EDI](./cmp_edi.md) |
| `k8s-fluentd`             | containers/fluentd | - | Model logs and feedback sender | [Feedback](./cmp_feedback.md)  |
| `k8s-feedback-aggregator` | containers/feedback-aggregator | legion/feedback-aggregator | API endpoint for Feedback API | [Feedback](./cmp_feedback.md)  |
| `k8s-operator`            | containers/operator/Dockerfile | legion/operator | Monitors Legion's CRDs and processes them | [CRDs](./ref_crds.md) [Operator](./cmp_operator.md) |
| `k8s-model-builder`       | containers/operator/Dockerfile | legion/operator | Sidecar for model training Pods. Manages training process | [Operator](./cmp_operator.md)|
| `python-toolchain`        | containers/toolchains/python/Dockerfile | legion/sdk, legion/cli, legion/toolchains/python | SDK for Python developers | [Python Toolchain](./tlch_python.md) |

### Docker images locations
* Release versions of images are on Docker Hub in [legionplatform](https://hub.docker.com/u/legionplatform) organization. Example image name: `legionplatform/k8s-edi`.
* Pre-release versions of images are on Docker Hub in [legionplatformtest](https://hub.docker.com/u/legionplatformtest) organization. Example image name: `legionplatformtest/k8s-edi`.
* Development versions of images are on [development server](nexus.cc.epm.kharlamov.biz:443/legion) that is not accessible from Internet, but accessible from CI/CD server. Example image name: `nexus-local.cc.epm.kharlamov.biz:443/legion/k8s-edi`.

## Python packages
Legion provides Legion SDK Python package ([Python toolchain](./tlch_python.md)) for development of ML models.

### Python SDK package location
* Release versions on Python package are on PyPi in project [legion](https://pypi.org/project/legion/).
* Pre-release and development versions of Python package are on [development server](https://nexus.cc.epm.kharlamov.biz/repository/pypi-proxy/) that is not accessible from Internet, but accessible from CI/CD server.