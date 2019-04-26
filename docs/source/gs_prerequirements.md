# Pre-requirements for on-cluster deploying

Legion requires ready Kubernetes cluster, HELM tool and Docker Registry (inside or outside the cluster).

### Kubernetes cluster
Legion platform could be deployed on bare-metal / PaaS Kubernetes cluster.

Kubernetes version required: at least 1.11.

### Installed HELM tool
Entire Legion platform is distributed as a HELM Chart and Docker images (details in [distros section](./gen_distros.md)) and you have to use [HELM tool](https://helm.sh/) to deploy legion on your cluster.

Currently Legion supports HELM (client and server) version **2** (at least **2.10** minor version).

### Docker Registry for model storing
Legion requires Docker Registry (Docker images storage), that should be accessible from the Kubelet of each node (Kubernetes daemon that are on each node) and from EDI Pods.

Docker images storage is used by Legion for storing trained models' images. And to deploy model images from.

URI of this Docker Registry and access credentials should be provided to HELM chart values during installation.

**WARNING:** It is required to allow anonymous pull access to this registry alongside authorized access (for EDI to inspecting labels).
