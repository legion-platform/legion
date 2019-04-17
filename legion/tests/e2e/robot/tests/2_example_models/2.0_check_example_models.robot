*** Settings ***
Documentation       Legion stack operational check
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Resource            ../../resources/keywords.robot
Library             legion.robot.libraries.prometheus.Prometheus  ${HOST_PROTOCOL}://prometheus.${HOST_BASE_DOMAIN}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Choose cluster context  ${CLUSTER_NAME}  AND
...                 Delete the examples models   AND
...                 Build the example models
Suite Teardown      Delete the examples models
Force Tags          operator  models  enclave  apps

*** Keywords ***
Delete the examples models
    [Documentation]  Delete built models
    :FOR  ${model_name}  IN  @{TEST_MODELS}
    \    Delete model training  ${model_name}

Build the example models
    [Documentation]  Start building models
    :FOR  ${model_name}  IN  @{TEST_MODELS}
    \    Create model training from yaml  examples/${model_name}/modeltraining.yaml

Test model pipeline result
    [Arguments]          ${model_name}
    Wait model training  ${model_name}
    ${model_build_status} =      Get model training status  ${model_name}
    Log                  Model build status is ${model_build_status}

    ${model_id}=        Get From Dictionary  ${model_build_status}  id
    ${model_version}=   Get From Dictionary  ${model_build_status}  version
    ${model_image}=     Get From Dictionary  ${model_build_status}  modelImage

    Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${model_image}  ${model_id}  ${model_version}

    ${edge}=             Build enclave EDGE URL  ${MODEL_TEST_ENCLAVE}
    Get token from EDI   ${MODEL_TEST_ENCLAVE}   ${model_id}   ${model_version}

    ${model_info} =      Get model info  ${edge}  ${TOKEN}  ${model_id}  ${model_version}
    Log                  Model info is ${model_info}

    ${edi_state}=        Run      legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN}
    Log                  State of ${model_id} is ${edi_state}

    Ensure metric present  ${model_id}  ${model_version}  ${MODEL_WITH_PROPS_ENDPOINT}

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Template]  Test model pipeline result
    model_name=Digit-Recognition
    model_name=Test-Summation