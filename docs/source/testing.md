# Testing

There are 2 test categories in legion:
* unit tests, located in `/legion/tests/unit`
* system/integration tests, located in `/legion/tests/e2e`
    * Python tests in `python` sub folder
    * Robot Framework tests in `robot` sub folder

## Running unit tests

```bash
make unittests
```

### Writing unit test with mocking Kubernetes API
In order to allow developers write unit tests that contains mocking of Kubernetes client API functions
`mock_swagger_function_response_from_file` and `persist_swagger_function_response_to_file` have been added to
`legion_test_utils`.

Function `mock_swagger_function_response_from_file` takes 2 arguments:
* name of API function like `'kubernetes.client.CoreV1Api.list_namespaced_service'`
* name/names of API *response codes* (saved responses) e.g. `'two_models'` or `['empty', 'two_models']`. Multiple *response codes* may be required if API is called more then one and for each call should be special response, in this case *response codes* will be used in right order (for 1st call - 1st response code, and etc.)

This function mocks API function and returns valid response, readed from file.

Path to data file is constructed as `<repo>/legion/tests/unit/data/responses/<funcion>.<response_type>.<reponse_code>.yaml`

Function `persist_swagger_function_response_to_file` has been added to simplify data files creation. It takes same arguments as a `mock_swagger_function_response_from_file` function. But it isn't change behaviour of standart API, it stores responses of API to disk. It stores data in directories that are reading by `mock_swagger_function_response_from_file`.

To write **new tests** with Kubernetes API mocks you have to:
* setup Kubernetes context to working cluster
* write new tests
* run tests and ensure that all of them are working
* persist responses via `persist_swagger_function_response_to_file` context manager
* remove all sensitive data from persisted responses
* change `persist_swagger_function_response_to_file` to `mock_swagger_function_response_from_file`
* remove Kubernetes connection context / disconnect from Internet
* run tests and ensure that all of them are working


## Running system/integration tests

We set up robot tests for `legion-test` cluster in the example below.
Do not forget change your cluster url and legion version.

* You should meet all requirements for unit tests
* You should add extra dependencies:
    1. kops, kubectl binaries
    2. aws credentials

* You should export kops context `kops export kubecfg --name legion-test.epm.kharlamov.biz --state s3://legion-cluster`

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