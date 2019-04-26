# Deploying on cluster

To deploy Legion on Kubernetes cluster, you have to:
* Authorize on cluster
* Install [HELM](./gs_prerequirements.md#installed-helm-tool) on cluster
* Install Legion CRD
```bash
helm install legion-crds --name legion-crds --repo https://github.com/legion-platform/legion-helm-charts
```
* Create configuration file for Legion HELM chart, e.g. `values.yaml` using these [documentation](./ref_configuration.md) or [examples](./ref_legion_helm_values_examples.md).
* Install Legion using configuration file
```bash
helm install legion -f values.yaml --name legion --repo https://github.com/legion-platform/legion-helm-charts
```

That's all, you can:
* [Train models](./gs_training_model.md)
* [Deploy models](./gs_deploying_model.md)
* View performance of deployed models (if monitoring integration is enabled, disabled by default).
* [Send feedback for made predictions](./gs_feedback_loop.md) and [read sent feedback](./gs_feedback_loop.md) (if feedback is enabled, disabled by default).
* [Query deployed models](./gs_querying_model.md) (if EDGE and Ingresses are enabled, ingress is disabled by default)
