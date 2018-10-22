# Testing

There are 2 test categories in legion:
* unit tests, located in `/legion/tests`
* system/integration tests, located in `/tests`
    * Python tests in `python` sub folder
    * Robot Framework tests in `robot` sub folder

## Running unit tests
There are some dependencies for running unit tests:
* You should install Python 3.6, docker (allow non-root user use docker)
* You should make develop version of legion package `python setup.py develop`

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
You should meet all requirements for unit tests
You should add extra dependencies:
    * kops, kubectl binaries
    * aws credentials
Firstly, you should export kops context `kops export kubecfg --name legion-test.epm.kharlamov.biz --state s3://legion-cluster`

Then, you have to start tests.

> To start app in telepresence you have to start app in special prepared environment. 
> `telepresence --also-proxy nexus-local.cc.epm.kharlamov.biz --method vpn-tcp --run bash`

