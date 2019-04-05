*** Settings ***
Documentation       Legion stack operational check
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Resource            ../../resources/keywords.robot
Library             legion.robot.libraries.prometheus.Prometheus  ${HOST_PROTOCOL}://prometheus.${HOST_BASE_DOMAIN}
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
    \    Test model pipeline result   ${model_name}   ${MODEL_TEST_ENCLAVE}