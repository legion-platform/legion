# Integration Testing

Legion uses the robotframework for an integration testing.
System/integration tests located in the following directories:
* `legion/robot` - a python package with additional Robot libraries. For example: kubernetes, auth_client, feedback, and so on. 
* `legion/tests/stuff` - artifacts for integration testing. For example: pre-trained ML artifacts, test toolchain integrations, and so on.
* `legion/tests/e2e` - directory with the RobotFramework tests.

## Running system/integration tests

We set up robot tests for `gke-legion-test` cluster in the example below.
*Do not forget change your cluster url and legion version.*

Export cluster secrets from legion-profiles directory.
* Clones *internal* legion-profiles repository. Checkout your or the developer branch.
* Clones [legion-infrastructure](https://github.com/legion-platform/legion-infrastructure) repository. Checkout your or the developer branch.
* Build terraform docker image using the `make docker-build-terraform` command in legion-infrastructure directory.
* You can optionally override the following parameters in `.env` file:
  * `CLUSTER_NAME`
  * `HIERA_KEYS_DIR`
  * `SECRET_DIR`
  * `CLOUD_PROVIDER`
  * `EXPORT_HIERA_DOCKER_IMAGE`
  * `LEGION_PROFILES_DIR`
* Executes `make export-hiera` command in the legion dir.
* Verify that `${SECRET_DIR}/.cluster_profile.json` file was created.

Updates the `.env` file when you should override a default Makefile option:
```bash
# Cluster name
CLUSTER_NAME=gke-legion-test
# Optionnaly, you can provide RobotFramework settings below.
# Additional robot parameters. For example, you can specify tags or variables.
ROBOT_OPTIONS=-e disable
# Robot files
ROBOT_FILES=**/*.robot
```

Afterward, you should set up a Legion cluster for RobotFramework tests using the `make setup-e2e-robot` command.
You should execute the previous command only once.

Finally, starts the robot tests:
```bash
make e2e-robot
```
