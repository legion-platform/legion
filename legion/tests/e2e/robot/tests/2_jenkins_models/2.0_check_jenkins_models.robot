*** Settings ***
Documentation       Legion stack operational check
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Resource            ../../resources/keywords.robot
<<<<<<< HEAD
Library             legion_test.robot.prometheus.Prometheus  ${HOST_PROTOCOL}://prometheus.${HOST_BASE_DOMAIN}
=======
Library             legion.robot.libraries.prometheus.Prometheus  ${HOST_PROTOCOL}://prometheus.${HOST_BASE_DOMAIN}
>>>>>>> [#849] sync refactoring
Library             Collections
Library             legion.robot.libraries.grafana.Grafana
Library             legion.robot.libraries.k8s.K8s
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.jenkins.Jenkins
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Choose cluster context                    ${CLUSTER_NAME}                         AND
...                 Run predefined Jenkins jobs for enclave   ${MODEL_TEST_ENCLAVE}
Force Tags          jenkins  models  enclave  apps

*** Keywords ***
Test model pipeline result
    [Arguments]          ${model_name}                      ${enclave}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    Log                  Model build meta is ${model_meta}
    ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    ${model_version} =   Get From Dictionary                ${model_meta}                 modelVersion
    ${edge}=             Build enclave EDGE URL             ${enclave}
    Get token from EDI   ${enclave}   ${model_id}   ${model_version}
    ${model_info} =      Get model info  ${edge}  ${TOKEN}  ${model_id}  ${model_version}
    Log                  Model info is ${model_info}
    ${edi_state}=        Run      legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN}
    Log                  State of ${model_id} is ${edi_state}
    Ensure metric present  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_ENDPOINT}
    [Return]             ${model_id}    ${model_version}

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    Connect to Jenkins endpoint
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
<<<<<<< HEAD
    \    Test model pipeline result   ${model_name}   ${MODEL_TEST_ENCLAVE}

Checking property update callback
    [Documentation]  Build and check model that uses property system
    [Tags]  props
    Connect to Jenkins endpoint
    ${model_id}    ${model_version} =   Test model pipeline result   ${MODEL_WITH_PROPS}   ${MODEL_TEST_ENCLAVE}
    Log   Model with id = ${model_id} and model_version = ${model_version} has been deployed
    ${edge}=        Build enclave EDGE URL  ${MODEL_TEST_ENCLAVE}
                    Get token from EDI      ${MODEL_TEST_ENCLAVE}   ${model_id}    ${model_version}

    Log   Resetting property to wrong value
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  0
    Log   Updating property to start value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  1

    Ensure model property has been updated  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_PROP}  1
    Ensure model API call result field is correct  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_ENDPOINT}  result  30   a=1  b=2

    Ensure metric present  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_ENDPOINT}

    Log   Updating property to another value and invoking model with check
    Update model property key  ${MODEL_TEST_ENCLAVE}  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_PROP}  2

    Ensure model property has been updated  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_PROP}  2
    Ensure model API call result field is correct  ${model_id}  ${model_version}  ${edge}  ${TOKEN}  ${MODEL_WITH_PROPS_ENDPOINT}  result  300   a=1  b=2
=======
    \    Test model pipeline result   ${model_name}   ${MODEL_TEST_ENCLAVE}
>>>>>>> [#849] sync refactoring
