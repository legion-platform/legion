*** Settings ***
Documentation       Check clusterwide and enclave resources
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${LEGION_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Force Tags          common

*** Test Cases ***
Checking if all enclave domains have been registered
    [Documentation]  Check that all required enclave DNS A records has been registered
    [Tags]  infra
    [Template]  Check domain exists
    edi.${HOST_BASE_DOMAIN}
    edge.${HOST_BASE_DOMAIN}
    mlflow.${HOST_BASE_DOMAIN}
    jupyterlab.${HOST_BASE_DOMAIN}

Checking if all replica sets, stateful sets, deployments are up and running
    [Documentation]  Gather information from kubernetes through API and check state of all required componens
    [Tags]  k8s
    [Template]  Deployment is running
    legion-edi                                   ${LEGION_NAMESPACE}
    legion-fluentd                               ${LEGION_NAMESPACE}
    legion-mlflow-legion-mlflow-tracking-server  ${LEGION_NAMESPACE}
