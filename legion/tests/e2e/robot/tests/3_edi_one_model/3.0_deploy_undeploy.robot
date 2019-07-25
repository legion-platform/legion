*** Variables ***
${LOCAL_CONFIG}        legion/config_3_1
${TEST_MT_NAME}        stub-model-3-1
${TEST_MD_NAME}        stub-model-3-1
${TEST_MODEL_NAME}     3
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.k8s.K8s  ${LEGION_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Library             legion.robot.libraries.edi.EDI  ${EDI_URL}  ${DEX_TOKEN}
Suite Setup         Run Keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Build model  ${TEST_MT_NAME}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  AND
...                               Get token from EDI  ${TEST_MD_NAME}  ${TEST_MD_NAME}  AND
...                               Run EDI undeploy model and check    ${TEST_MD_NAME}

Suite Teardown      Run Keywords  Delete model training  ${TEST_MT_NAME}  AND
...                               Run EDI undeploy model and check    ${TEST_MD_NAME}
Test Setup          Run EDI deploy and check model started            ${TEST_MD_NAME}   ${TEST_MODEL_IMAGE}   ${TEST_MODEL_NAME}    ${TEST_MODEL_VERSION}  ${TEST_MD_NAME}
Test Teardown       Run EDI undeploy model and check    ${TEST_MD_NAME}
Force Tags          edi  cli  enclave

*** Keywords ***
Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose md create -f ${LEGION_ENTITIES_DIR}/md/${create_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MD_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  0/1/1

    ${res}=  Shell  legionctl --verbose md edit -f ${LEGION_ENTITIES_DIR}/md/${edit_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MD_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  0/1/2

    ${res}=  Shell  legionctl --verbose md delete -f ${LEGION_ENTITIES_DIR}/md/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MD_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose md ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose md ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Provide name of a Model Deployment or path to a file

*** Test Cases ***
Check EDI deploy procedure
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                      ${TEST_MD_NAME}   ${TEST_MODEL_IMAGE}  ${TEST_MD_NAME}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${response}=    Wait Until Keyword Succeeds  1m  0 sec  Check model started  ${TEST_MD_NAME}
                    Should contain                      ${response}         'model_version': '${TEST_MODEL_VERSION}'

Check EDI invalid model name deploy procedure
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    [Documentation]  Try to deploy dummy invalid model name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell                legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE}test --timeout 30
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Time out

Deploy with custom memory and cpu
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    [Documentation]  Deploy with custom memory and cpu
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --memory-limit 333Mi --cpu-limit 333m --memory-request 222Mi --cpu-request 222m
         Should be equal  ${res.rc}  ${0}

    ${md_status} =      Get model deployment status  ${TEST_MD_NAME}
    Log                  Model build status is ${md_status}
    ${model_deployment_name}=      Get From Dictionary  ${md_status}  deployment

    ${model_deployment}=  Get model deployment  ${model_deployment_name}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  333m  ${model_resources.limits["cpu"]}
    Should be equal  333Mi  ${model_resources.limits["memory"]}
    Should be equal  222m  ${model_resources.requests["cpu"]}
    Should be equal  222Mi  ${model_resources.requests["memory"]}

Check setting of default resource values
    [Documentation]  Deploy setting of default resource values
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE}
             Should be equal  ${res.rc}  ${0}

    ${md_status} =      Get model deployment status  ${TEST_MD_NAME}
    Log                  Model build status is ${md_status}
    ${model_deployment_name}=      Get From Dictionary  ${md_status}  deployment

    ${model_deployment}=  Get model deployment  ${model_deployment_name}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  256m  ${model_resources.limits["cpu"]}
    Should be equal  256Mi  ${model_resources.limits["memory"]}
    Should be equal  128m  ${model_resources.requests["cpu"]}
    Should be equal  128Mi  ${model_resources.requests["memory"]}

Check commands with file parameters
    [Documentation]  Model Deployment commands with differenet file formats
    [Setup]  None
    [Teardown]  None
    [Template]  Check commands with file parameter
    create_file=k8s.json     edit_file=k8s-changed.yaml     delete_file=k8s-changed

File with entitiy not found
    [Documentation]  Invoke Model Deployment commands with not existed file
    [Setup]  None
    [Teardown]  None
    [Template]  File not found
    command=create
    command=edit

User must specify filename or mt name
    [Documentation]  Invoke Model Deployment commands without paramteres
    [Setup]  None
    [Teardown]  None
    [Template]  Invoke command without parameters
    command=create
    command=edit
