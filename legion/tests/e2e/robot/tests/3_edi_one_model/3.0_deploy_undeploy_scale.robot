*** Variables ***
${LOCAL_CONFIG}        legion/config_3_1
${TEST_MODEL_NAME}     stub-model-3-1
${TEST_MODEL_ID}       3
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run Keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                               Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                               Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
Suite Teardown      Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}
Test Setup          Run EDI deploy and check model started            ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}   ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
Test Teardown       Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
Force Tags          edi  cli  enclave

*** Keywords ***
Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose md create -f ${LEGION_ENTITIES_DIR}/md/${create_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MODEL_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  1/1

    ${res}=  Shell  legionctl --verbose md edit -f ${LEGION_ENTITIES_DIR}/md/${edit_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MODEL_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  2/2

    ${res}=  Shell  legionctl --verbose md delete -f ${LEGION_ENTITIES_DIR}/md/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get ${TEST_MODEL_NAME}
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
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                      ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${response}=    Check model started                 ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                      ${response}         'model_version': '${TEST_MODEL_VERSION}'

Check EDI deploy with scale to 1
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --replicas 1
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                 ${response}         'model_version': '${TEST_MODEL_VERSION}'

    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated  1/1

Check EDI deploy with scale to 2
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                 ${response}             'model_version': '${TEST_MODEL_VERSION}'

    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2/2

Check EDI invalid model name deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy invalid model name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell                legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}test
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Label extraction from ${TEST_MODEL_IMAGE}test image is failed

Check EDI double deploy procedure for the same model
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy twice the same dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
                    Should Be Equal As Integers   ${resp.rc}         0
    ${response}=    Check model started           ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                ${response}             'model_version': '${TEST_MODEL_VERSION}'
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
                    should not be equal as integers  ${resp.rc}         0
    ${response}=    Check model started           ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                ${response}             'model_version': '${TEST_MODEL_VERSION}'

Check EDI undeploy procedure
    [Documentation]  Try to undeploy dummy valid model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers         ${resp.rc}         0
                    Should not contain                  ${resp.stdout}     ${TEST_MODEL_NAME}

Check EDI scale up procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}           0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2/2

Check EDI scale down procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2/2

    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 1
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   1/1

Check EDI invalid model id scale up procedure
    [Documentation]  Try to scale up dummy model with invalid name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME}-wrong --replicas 2
                    Should Be Equal As Integers  ${resp.rc}         2
                    Should contain               ${resp.stderr}     not found

Deploy with custom memory and cpu
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Deploy with custom memory and cpu
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --memory-limit 333Mi --cpu-limit 333m --memory-request 222Mi --cpu-request 222m
         Should be equal  ${res.rc}  ${0}
    ${model_deployment}=  Get model deployment  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${MODEL_TEST_ENCLAVE}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  333m  ${model_resources.limits["cpu"]}
    Should be equal  333Mi  ${model_resources.limits["memory"]}
    Should be equal  222m  ${model_resources.requests["cpu"]}
    Should be equal  222Mi  ${model_resources.requests["memory"]}

Check setting of default resource values
    [Documentation]  Deploy setting of default resource values
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
             Should be equal  ${res.rc}  ${0}
    ${model_deployment}=  Get model deployment  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${MODEL_TEST_ENCLAVE}
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
    [Template]  File not found
    command=create
    command=edit

User must specify filename or mt name
    [Documentation]  Invoke Model Deployment commands without paramteres
    [Template]  Invoke command without parameters
    command=create
    command=edit
