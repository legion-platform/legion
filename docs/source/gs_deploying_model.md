================
Deploying models
================

Legion supports deploying [Legion-compatible models](./gs_what_is_model.md) on top of cluster or on any machine with installed Docker Engine. This chapter describes on-cluster deployment. For local deployment please refer [local mode section](./gs_local_run.md).

**WARNING: Not every Docker Image can be deployed on Legion. Legion only supports deploying of [compatible models](./gs_what_is_model.md#built-model).**

To deploy Legion model on top of cluster next mechanisms can be used:
* Creationing of [ModelDeployment CR](./ref_crds.md).
* Using `legionctl` tool. [See chapter](./cmp_legionctl.md).
* Calling EDI service using HTTP requests.

Each deployed model is available to:
* Be queried using HTTP API. [See chapter](./gs_querying_model.md)
* Be scaled using `legionctl` / EDI call.
* Be undeployed (using same ways as for deployment).

## Examples of VCS credentials management

### Using `kubectl`

```bash
kubectl create -f - <<EOF
apiVersion: legion.legion-platform.org/v1alpha1
kind: VCSCredential
metadata:
  name: vcs-examlpe
spec:
  credential: bG9sa2VrbG9sa2VrCg==
  defaultReference: master
  type: git
  uri: git@github.com:legion-platform/legion.git
EOF
```

### Using `legionctl`

```bash
legionctl vcs create vcs-examlpe \
          --type git \
          --uri git@github.com:legion-platform/legion.git \
          --default-reference master \
          --credential "bG9sa2VrbG9sa2VrCg=="
```

### Using Plain HTTP

```bash
curl -X POST "https://<edi-url>/api/v1/vcs" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{ "name": "vcs-examlpe", "spec": { "credential": "bG9sa2VrbG9sa2VrCg==", "defaultReference": "master", "type": "git", "uri": "git@github.com:legion-platform/legion.git" }}'
```


## Examples of training management

### Using `kubectl`

```bash
kubectl create -f - <<EOF
apiVersion: legion.legion-platform.org/v1alpha1
kind: ModelDeployment
metadata:
  name: deployment-example
spec:
  image: <docker-repository>/legion/example:1.0
  replicas: 2
EOF
```

### Using `legionctl`

```bash
legionctl md create deployment-example \
          --image <docker-repository>/legion/example:1.0 \
          --replicas 2
```

### Using Plain HTTP

```bash
curl -X POST "https://<edi-url>/api/v1/model/deployment" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"name":"deployment-example","spec": {"image":"<docker-repository>/legion/example:1.0","replicas": 2 }}'
```
