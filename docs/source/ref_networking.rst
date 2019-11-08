==========
Networking
==========

By default, Legion does not provide NetworkPolicy instances, but any policy that uses Pod label
selection may be used (e.g. K8S NetworkPolicy).

Network rules
-------------
Legion components require communication between:

* Operator, Trainer, Packager, and Deployer instances
* EDI and Deployer instances
* EDGE and Deployer instances
* EDI and Docker Registry
* Cluster ingress controller and EDGE
* Trainer instances and statsd (in external namespace)
* Prometheus and Legion components -- for exporting performance metrics
* EDGE and feedback components (aggregator and FluentD) -- for feedback loop
