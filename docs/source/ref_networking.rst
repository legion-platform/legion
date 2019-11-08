==========
Networking
==========

By default, Legion does not provide NetworkPolicy instances, but any policy that uses Pod label
selection may be used (e.g. K8S NetworkPolicy).

Network rules
-------------

Legion components require some intra-pod communication:

* Connection between Operator, Trainers, Packagers, and Deployer
* Connection between EDI and Deployer instances
* Connection between EDGE and Deployer instances
* Connection between EDI and Docker Registry
* Connection between cluster's ingress controller and EDGE
* Connection between Trainer instances and statsd (in external namespace)
* Connection between Prometheus and Legion's components -- for exporting performance metrics
* Connection between EDGE and feedback components (aggregator and FluentD) -- for feedback loop
