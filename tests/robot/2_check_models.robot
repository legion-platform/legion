*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.K8s
Library             legion_test.robot.Utils
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Model
Test Setup          Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Tags]  jenkins  models  enclave
    Connect to Jenkins endpoint
    Run, wait and check jenkins jobs for enclave     ${MODEL_TEST_ENCLAVE}

Checking property update callback
    [Documentation]  Build and check model that uses property system
    [Tags]  jenkins  models  enclave  props
    Connect to Jenkins endpoint
    ${model_id}    ${model_version} =   Test model pipeline  ${MODEL_WITH_PROPS}  ${MODEL_TEST_ENCLAVE}
    Log                                 Model with id = ${model_id} and version = ${model_version} has been deployed
    ${edge}=        Build enclave EDGE URL  ${MODEL_TEST_ENCLAVE}

    Log             Updating property to start value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  1

    ${properties}=  Get model API properties  ${model_id}  ${model_version}  ${edge}
    Should Be Equal As Integers     ${properties[MODEL_WITH_PROPS_PROP]}  1

    ${response}=    Invoke model API  ${model_id}  ${model_version}  ${edge}  ${MODEL_WITH_PROPS_ENDPOINT}  a=1  b=2
    Should Be Equal As Integers     ${response['result']}  30

    Log             Updating property to another value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  2

    ${properties}=  Get model API properties  ${model_id}  ${model_version}  ${edge}
    Should Be Equal As Integers     ${properties[MODEL_WITH_PROPS_PROP]}  2

    ${response}=    Invoke model API  ${model_id}  ${model_version}  ${edge}  ${MODEL_WITH_PROPS_ENDPOINT}  a=1  b=2
    Should Be Equal As Integers     ${response['result']}  300

Check Vertical Scailing
    [Documentation]  Runs "PERF TEST Vertical-Scaling" jenkins job to test vertical scailing
    [Tags]  jenkins model
    :FOR  ${enclave}    IN    @{ENCLAVES}
    \  Connect to Jenkins endpoint
        Run Jenkins job                                         PERF TEST Vertical-Scaling   Enclave=${enclave}
        Wait Jenkins job                                        PERF TEST Vertical-Scaling   600
        Last Jenkins job is successful                          PERF TEST Vertical-Scaling
