# Model development

Legion supports:
* [Local model development (training)](./gs_local_run.md)
* [Cloud model training](#cloud-model-training).

## Cloud model training.
To train model on a cluster, next actions should be performed:
1. Source code of model should be pushed in Source Code Repository
2. [VCSCredential CR](./ref_crds.md) with credentials to Source Code repository should exist.
3. [ModelTraining CR](./ref_crds.md) with appropriate parameters should be created.

To simplify management of CRs (VCSCredential / ModelTraining) legion provides:
* HTTP management API (handled by EDI)
* `legionctl` management tool

## Example

### Using `kubectl`

```bash
kubectl create -f - <<EOF
apiVersion: legion.legion-platform.org/v1alpha1
kind: ModelTraining
metadata:
  name: training-example
spec:
  toolchain: jupyter
  vcsName: training-example
  entrypoint: "<path-to-notebook>"
EOF
```

### Using `legionctl`

```bash
legionctl --verbose mt create training-example \
          --timeout 300 \
          --toolchain jupyter \
          --vcs training-example \
          -e '<path-to-notebook>'
```

### Using Plain HTTP

```bash
curl -X POST "https://<edi-url>/api/v1/model/training" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"name": "training-example","spec": {"entrypoint": "<path-to-notebook>","toolchain": "jupyter", "vcsName": "training-example"}}'
```

