*** Settings ***
Documentation       Check clusterwide and enclave resources
Resource            resources/browser.robot
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ../deploy/profiles/
Library             Collections
Library             legion_test.robot.K8s
Library             legion_test.robot.Utils
Test Teardown       Close All Browsers

*** Test Cases ***
Checking if all core domains have been registered
    [Documentation]  Check that all required core DNS A records has been registered
    [Tags]  core  dns
    :FOR    ${subdomain}    IN    @{SUBDOMAINS}
    \  Check domain exists  ${subdomain}.${HOST_BASE_DOMAIN}


Checking if all enclave domains have been registered
    [Documentation]  Check that all required enclave DNS A records has been registered
    [Tags]  core  dns
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \   Check if all enclave domains are registered      ${enclave}

Checking if all replica sets, stateful sets, replication controllers are up and running
    [Documentation]  Gather information from kubernetes through API and check state of all required componens
    [Tags]  k8s
    Replica set is running                   ${DEPLOYMENT}-core-nexus
    Replication controller is running        ${DEPLOYMENT}-core-jenkins
    Replication controller is running        ${DEPLOYMENT}-core-graphite
    Replication controller is running        ${DEPLOYMENT}-core-console
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Replication controller is running        ${DEPLOYMENT}-${enclave}-edge          ${enclave}
    \  Replication controller is running        ${DEPLOYMENT}-${enclave}-edi           ${enclave}
    \  Replication controller is running        ${DEPLOYMENT}-${enclave}-grafana       ${enclave}
    \  Replication controller is running        ${DEPLOYMENT}-${enclave}-graphite      ${enclave}

Check Nexus availability
    [Documentation]  Check Nexus UI availability
    [Tags]  nexus  ui
    Open Nexus                              /
    Wait Nexus componens in menu

Check Nexus Components available
    [Documentation]  Check that Nexus storages (components) are ready
    [Tags]  nexus  ui
    Open Nexus                              /#browse/browse/components
    ${componentNames}=                      Get Nexus components table
#    List Should Contain Value               ${componentNames}           docker-hosted
#    List Should Contain Value               ${componentNames}           raw

Check Console availability
    [Documentation]  Check Console UI availability
    [Tags]  ui
    Open Console                              /

Check enclave EDI availability
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  ${edi_state} =           Run EDI inspect  ${enclave}
    \  Should not contain       ${edi_state}   legionctl: error
    \  Should not contain       ${edi_state}   Exception

Check enclave Grafana availability
    [Documentation]  Try to connect to Grafana in each enclave
    [Tags]  grafana  enclave
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Grafana     ${enclave}

