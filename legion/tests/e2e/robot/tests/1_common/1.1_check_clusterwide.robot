*** Settings ***
Documentation       Check clusterwide and enclave resources
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Suite Setup        Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Checking if all enclave domains have been registered
    [Documentation]  Check that all required enclave DNS A records has been registered
    [Tags]  core  dns  infra
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \   Check if all enclave domains are registered      ${enclave}

Checking if all replica sets, stateful sets, deployments are up and running
    [Documentation]  Gather information from kubernetes through API and check state of all required componens
    [Tags]  k8s  infra
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Deployment is running   ${DEPLOYMENT}-edge          namespace=${enclave}
    \  Deployment is running   ${DEPLOYMENT}-edi           namespace=${enclave}

Check Vertical Scailing
    [Documentation]  Start the fat pod to test vertical scailing
    [Tags]  k8s  scaling  infra
    [Setup]  Delete fat pod
    [Teardown]  Delete fat pod

    Start fat pod  ${NODE_TAINT_KEY}  ${NODE_TAINT_VALUE}
    Wait fat pod completion
    Delete fat pod

    Wait nodes scale down  ${NODE_TAINT_KEY}  ${NODE_TAINT_VALUE}  1800
