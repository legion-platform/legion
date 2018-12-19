# Testing

There are 2 test categories in legion:
* unit tests, located in `/legion/tests`
* system/integration tests, located in `/tests`
    * Python tests in `python` sub folder
    * Robot Framework tests in `robot` sub folder

## Running unit tests
There are some dependencies for running unit tests:
* You should install Python 3.6, docker (allow non-root user use docker)
* You should build base python image:
```bash
cd base-python-image
docker build --network host -t legion/base-python-image:latest .
```
* You should create virtualenv and donwload main and develop dependencies
* You should make develop version of legion package:
```bash
cd legion
python setup.py develop
python setup.py collect_data
```

Run tests:
```bash
cd legion/tests
nosetests --processes=10 --process-timeout=600
```

### Writing unit test with mocking Kubernetes API
In order to allow developers write unit tests that contains mocking of Kubernetes client API functions
`mock_swagger_function_response_from_file` and `persist_swagger_function_response_to_file` have been added to
`legion_test_utils`.

Function `mock_swagger_function_response_from_file` takes 2 arguments:
* name of API function like `'kubernetes.client.CoreV1Api.list_namespaced_service'`
* name/names of API *response codes* (saved responses) e.g. `'two_models'` or `['empty', 'two_models']`. Multiple *response codes* may be required if API is called more then one and for each call should be special response, in this case *response codes* will be used in right order (for 1st call - 1st response code, and etc.)

This function mocks API function and returns valid response, readed from file.

Path to data file is constructed as `<repo>/legion/tests/data/responses/<funcion>.<response_type>.<reponse_code>.yaml`

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
* Create the `.secret.yaml` file
```yaml
dex:
  enabled: true
  config:
    staticPasswords:
      - email: tests-user@legion.com
        password: ~
```
* Export the following environment variables:
```bash
export PROFILE="legion-test.epm.kharlamov.biz"
export LEGION_VERSION="0.10.0-20181213084714.1329.6ba06cc"
export PATH_TO_COOKIES="credentials.secret"
export CLUSTER_NAME="legion-test.epm.kharlamov.biz"
export CREDENTIAL_SECRETS=".secrets.yaml"
export ROBOT_OPTIONS="-v PATH_TO_PROFILES_DIR:../../deploy/profiles"
```

* Finally, start the robot tests, for example:
```bash
cd tests/robot
robot tests/3_edi_one_model/3.0_check_edi_one_model.robot
```

> To start app in telepresence you have to start app in special prepared environment. 
> `telepresence --also-proxy nexus-local.cc.epm.kharlamov.biz --method vpn-tcp --run bash`

