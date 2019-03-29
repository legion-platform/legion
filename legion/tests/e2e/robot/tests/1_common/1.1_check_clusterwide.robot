*** Settings ***
Documentation       Check clusterwide and enclave resources
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion.robot.libraries.k8s.K8s
Library             legion.robot.libraries.utils.Utils
Test Setup          Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Checking if all core domains have been registered
    [Documentation]  Check that all required core DNS A records has been registered
    [Tags]  core  dns  infra
    :FOR    ${subdomain}    IN    @{SUBDOMAINS}
    \  Check domain exists  ${subdomain}.${HOST_BASE_DOMAIN}

Checking if all enclave domains have been registered
    [Documentation]  Check that all required enclave DNS A records has been registered
    [Tags]  core  dns  infra
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \   Check if all enclave domains are registered      ${enclave}

Checking if all replica sets, stateful sets, deployments are up and running
    [Documentation]  Gather information from kubernetes through API and check state of all required componens
    [Tags]  k8s  infra
    Deployment is running        ${DEPLOYMENT}-core-jenkins   namespace=default
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Deployment is running   ${DEPLOYMENT}-${enclave}-edge          namespace=${enclave}
    \  Deployment is running   ${DEPLOYMENT}-${enclave}-edi           namespace=${enclave}

Grafana preferences contains main dashboard
    [Documentation]  Check that main dashboard sets as home and stars
    [Tags]  grafana  infra
    LOG  ${GRAFANA_USER}
    LOG  ${GRAFANA_PASSWORD}
    Connect to main Grafana

    ${PREFERENCES}=  Get preferences
    ${MAIN_DASHBOARD}=  Get dashboard by  uid=${GRAFANA_MAIN_DASHBOARD_UID}
    should be equal  &{PREFERENCES}[homeDashboardId]  ${MAIN_DASHBOARD["dashboard"]["id"]}
    should be true  ${MAIN_DASHBOARD["meta"]["isStarred"]}

Check Vertical Scailing
    [Documentation]  Runs "PERF TEST Vertical-Scaling" jenkins job to test vertical scailing
    [Tags]  k8s  scaling  infra
    Get cluster nodes and their count    before

    :FOR  ${enclave}    IN    @{ENCLAVES}
    \  Connect to Jenkins endpoint
        Run Jenkins job                  PERF TEST Vertical-Scaling   Enclave=${enclave}
        Wait Jenkins job                 PERF TEST Vertical-Scaling   780
        Last Jenkins job is successful   PERF TEST Vertical-Scaling

    Get cluster nodes and their count    after
    Should Not Be Equal As Integers    ${NODES_COUNT_BEFORE}    ${NODES_COUNT_AFTER}
    Wait node scale down           ${NODES_COUNT_BEFORE}  900
