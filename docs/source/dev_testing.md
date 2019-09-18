# Testing

There are 2 test categories in legion:
* unit tests, located in `legion/tests/unit`
* system/integration tests, located in `legion/tests/e2e`
    * Python tests in `python` sub folder
    * Robot Framework tests in `robot` sub folder
    * Stub models in `models` sub folder (are used for Robot Framework tests as payloads)

## Running unit tests

```bash
make unittests
```

## Running system/integration tests

We set up robot tests for `legion-test` cluster in the example below.
Do not forget change your cluster url and legion version.

* You should meet all requirements for unit tests
* You should add extra dependencies:
    1. kops, kubectl binaries
    2. aws credentials (for calling `kops export`), if you test cluster that is created using kops

* You should export kops context `kops export kubecfg --name legion-test.epm.kharlamov.biz --state s3://legion-cluster` (for kops created cluster) or authorize on cluster using any other mechanism.

* Create the `.secret.yaml` file in the root folder. Fill all value gaps:

```yaml
dex:
  enabled: true
  config:
    staticPasswords:
      - email: tests-user@legion.com
        password: ~

grafana:
  admin:
    username: ~
    password: ~
```

* Create the `.env` file :
```bash
# Legion version
LEGION_VERSION=0.11.0
# Cluster name
CLUSTER_NAME=legion-test.epm.kharlamov.biz
# Additional robot parameters. For example, you can specify tags or variables.
ROBOT_OPTIONS=
# Robot files
ROBOT_FILES=**/*.robot
```

* Finally, start the robot tests, for example:
```bash
make e2e-robot
```

Or python integration tests:
```bash
make e2e-python
```