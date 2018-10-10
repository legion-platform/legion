*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion_test.robot.K8s
Library             legion_test.robot.Utils
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Model
Suite Setup         Run Keywords
...                 Choose cluster context                    ${CLUSTER_NAME}                         AND
...                 Run predefined Jenkins jobs for enclave   ${MODEL_TEST_ENCLAVE}

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Tags]  jenkins  models  enclave
    Connect to Jenkins endpoint
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
    \    Test model pipeline result   ${model_name}   ${MODEL_TEST_ENCLAVE}

Checking property update callback
    [Documentation]  Build and check model that uses property system
    [Tags]  jenkins  models  enclave  props
    Connect to Jenkins endpoint
    ${model_id}    ${model_version} =   Test model pipeline result   ${MODEL_WITH_PROPS}   ${MODEL_TEST_ENCLAVE}
    Log                                 Model with id = ${model_id} and version = ${model_version} has been deployed
    ${edge}=        Build enclave EDGE URL  ${MODEL_TEST_ENCLAVE}
                    Get token from EDI      ${MODEL_TEST_ENCLAVE}

    Log             Resetting property to wrong value
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  0
    Log             Updating property to start value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  1

    Ensure model property has been updated  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_PROP}  1
    Ensure model API call result field is correct  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_ENDPOINT}  result  30   a=1  b=2

    Log             Updating property to another value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  2

    Ensure model property has been updated  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_PROP}  2
    Ensure model API call result field is correct  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_ENDPOINT}  result  300   a=1  b=2

Check Vertical Scailing
    [Documentation]  Runs "PERF TEST Vertical-Scaling" jenkins job to test vertical scailing
    [Tags]  jenkins  model  scaling
    Get cluster nodes and their count    before

    :FOR  ${enclave}    IN    @{ENCLAVES}
    \  Connect to Jenkins endpoint
        Run Jenkins job                                         PERF TEST Vertical-Scaling   Enclave=${enclave}
        Wait Jenkins job                                        PERF TEST Vertical-Scaling   600
        Last Jenkins job is successful                          PERF TEST Vertical-Scaling

    Get cluster nodes and their count    after
    Should Not Be Equal As Integers    ${NODES_COUNT_BEFORE}    ${NODES_COUNT_AFTER}
    Wait node scale down           ${NODES_COUNT_BEFORE}