*** Settings ***
Documentation       Check if all core components are secured
Resource            resources/browser.robot
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion_test.robot.K8s
Library             legion_test.robot.Utils
Test Setup          Choose cluster context            ${CLUSTER_NAME}
Test Teardown       Close All Browsers

*** Test Cases ***
Check if K8S dashboard domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=dashboard    enclave=${EMPTY}

Check if Jenkins domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=jenkins    enclave=${EMPTY}

Check if Nexus domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=nexus    enclave=${EMPTY}

Check if Grafana domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=grafana    enclave=${EMPTY}

Check if Grafana enclave domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if Airflow enclave domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=airflow    enclave=${MODEL_TEST_ENCLAVE}

Check if Flower enclave domain has been secured
    [Tags]  core  security   auth
    [Template]    Check if component domain has been secured
    component=flower    enclave=${MODEL_TEST_ENCLAVE}

Check if K8S dashboard domain does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=dashboard    enclave=${EMPTY}

Check if Jenkins domain does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=jenkins    enclave=${EMPTY}

Check if Nexus domain does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=nexus    enclave=${EMPTY}

Check if Grafana domain does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=grafana    enclave=${EMPTY}

Check if Grafana enclave does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if Airflow enclave does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=airflow    enclave=${MODEL_TEST_ENCLAVE}

Check if Flower enclave domain does not auth with invalid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=flower    enclave=${MODEL_TEST_ENCLAVE}

Check if Jenkins domain can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=jenkins    enclave=${EMPTY}

Check if Grafana enclave can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if Airflow enclave can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=airflow    enclave=${MODEL_TEST_ENCLAVE}

Check if Flower enclave can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=flower    enclave=${MODEL_TEST_ENCLAVE}

Check if K8S dashboard domain can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=Dashboard    enclave=${EMPTY}

Check if Nexus domain can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=nexus    enclave=${EMPTY}

Check if Grafana domain can auth with valid creds
    [Tags]  core  security   auth
    [Template]    Secured component domain should be accessible by valid credentials
    component=grafana    enclave=${EMPTY}