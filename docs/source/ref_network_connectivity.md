# Network rules

By default Legion does not provide any NetworkPolicy instances. But Legion installation can be secured using any policy that uses Pod label selection (like standard K8S NetworkPolicy).

## Network rules
You can use principle of least privilege that denies any connection in cluster and ingress/egress connection, but Legion components requires some in-cluster connections (between Pods) for keeping working.

* Connection between [Operator](./cmp_operator.md) and model training and model deployment instances - for inspecting training and deployed models
* Connection between [EDI](./cmp_edi.md) and model deployment instances - for inspecting deployed models
* Connection between [EDGE](./cmp_edge.md) and model deployment instances - for routing model API traffic
* Connection between [EDI](./cmp_edi.md) and Docker Registry that is used for storing trained models - for inspecting meta-information about images before deploy
* Connection between cluster's Ingress controller (nginx-ingress or etc.) and [EDGE](./cmp_edge.md) (for model API) and [EDI](./cmp_edi.md) (for manage API)
* Connection between training instances and statsd (in external namespace) - for storing train metrics
* Connection between Prometheus and Legion's components - for exporting performance metrics
* Connection between [EDGE](./cmp_edge.md) and feedback components (aggregator and FluentD) -- for feedback loop