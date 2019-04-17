*** Settings ***
Documentation       Check if all core components are secured
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Force Tags          core  security  auth
Test Setup          Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Check if K8S dashboard domain has been secured
    [Tags]  infra
    [Template]    Check if component domain has been secured
    component=dashboard    enclave=${EMPTY}

Check if Grafana domain has been secured
    [Tags]  infra
    [Template]    Check if component domain has been secured
    component=grafana    enclave=${EMPTY}

Check if Prometheus domain has been secured
    [Tags]  infra
    [Template]    Check if component domain has been secured
    component=prometheus    enclave=${EMPTY}

Check if alertmanager domain has been secured
    [Tags]  infra
    [Template]    Check if component domain has been secured
    component=alertmanager    enclave=${EMPTY}

Check if K8S dashboard domain does not auth with invalid creds
    [Tags]  infra
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=dashboard    enclave=${EMPTY}

Check if Grafana domain does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=grafana    enclave=${EMPTY}

Check if Prometheus domain does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=prometheus    enclave=${EMPTY}

Check if Alertmanager domain does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=alertmanager    enclave=${EMPTY}

Check if K8S dashboard domain can auth with valid creds
    [Tags]  infra
    [Template]    Secured component domain should be accessible by valid credentials
    component=Dashboard    enclave=${EMPTY}

Check if Grafana domain can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=grafana    enclave=${EMPTY}

Check if Prometheus domain can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=prometheus    enclave=${EMPTY}

Check if ALertmanager domain can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=Alertmanager    enclave=${EMPTY}

Service url stay the same after log in
    [Tags]  apps
    [Documentation]  Service url stay the same after log in
    [Template]    Url stay the same after dex log in
    service_url=https://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/healthcheck?xx=22&yy=33
    service_url=https://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/info?xx=22&yy=33
    service_url=https://grafana.${HOST_BASE_DOMAIN}/?orgId=1&x=2
    service_url=https://prometheus.${HOST_BASE_DOMAIN}/graph?x=2&y=3
    service_url=https://alertmanager.${HOST_BASE_DOMAIN}/?orgId=1&x=2
