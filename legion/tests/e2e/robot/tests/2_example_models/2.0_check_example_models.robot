*** Variables ***
${LOCAL_CONFIG}         legion/config_2_0

*** Settings ***
Documentation       Legion stack operational check
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Resource            ../../resources/keywords.robot
Library             legion.robot.libraries.prometheus.Prometheus  ${PROMETHEUS_URL}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${LEGION_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Library             legion.robot.libraries.edi.EDI  ${EDI_URL}  ${DEX_TOKEN}
Suite Setup         Run Keywords
...                 Choose cluster context  ${CLUSTER_NAME}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Delete the examples models
Suite Teardown      Delete the examples models
Force Tags          operator  models  enclave  apps

*** Keywords ***
Delete the examples models
    [Documentation]  Delete built models
    :FOR  ${model_name}  IN  @{TEST_MODELS}
    \    ${model_name_lower}=  Convert To Lowercase  ${model_name}
    \    StrictShell  legionctl --verbose mt delete ${model_name_lower} --ignore-not-found
    \    StrictShell  legionctl --verbose md delete ${model_name_lower} --ignore-not-found

Test model pipeline result
    [Arguments]          ${md_name}
    StrictShell  legionctl --verbose mt create -f examples/${md_name}/modeltraining.legion.yaml
    ${md_name}=  Convert To Lowercase  ${md_name}

    ${mt} =      Get model training  ${md_name}
    Log                  Model training is ${mt}

    ${model_name}=      set variable  ${mt.model_name}
    ${model_version}=   set variable  ${mt.model_version}
    ${model_image}=     set variable  ${mt.trained_image}

    Get token from EDI  ${md_name}

    Run EDI deploy and check model started  ${md_name}  ${model_image}  ${model_name}  ${model_version}

    ${model_info} =      Shell  legionctl --verbose model info --md ${md_name}
    Log                  Model info is ${model_info}

    ${md_state}=        StrictShell    legionctl --verbose md get ${md_name}
    ${edi_state}=       StrictShell    legionctl --verbose mr get ${md_name}

    Ensure metric present  ${model_name}  ${model_version}  ${MODEL_WITH_PROPS_ENDPOINT}

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Template]  Test model pipeline result
    md_name=Digit-Recognition
    md_name=Test-Summation
    md_name=Sklearn-Income