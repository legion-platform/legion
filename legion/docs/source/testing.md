# Testing

There are 2 test categories in legion:
* unit tests, located in `/legion/tests`
* system/integration tests, located in `/tests`
    * Python tests in `python` sub folder
    * Robot Framework tests in `robot` sub folder
    
## Running unit tests
There are some dependencies for running unit tests:
* You should install Python 3.5+, docker (allow non-root user use docker)
* You should make develop version of legion package `python setup.py develop`

## Running system/integration tests
You should meet all requirements for unit tests
You should add extra dependencies:
    * kops, kubectl binaries
    * aws credentials
Firstly, you should export kops context `kops export kubecfg --name legion-test.epm.kharlamov.biz --state s3://legion-cluster`

Then, you have to start tests.

> To start app in telepresence you have to start app in special prepared environment. 
> `telepresence --also-proxy nexus-local.cc.epm.kharlamov.biz --method vpn-tcp --run bash`

