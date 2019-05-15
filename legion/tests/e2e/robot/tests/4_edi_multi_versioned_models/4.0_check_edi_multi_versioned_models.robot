*** Variables ***
${LOCAL_CONFIG}  legion/config_4_0
${TEST_MODEL_ID}         4
${TEST_MODEL_VERSION_1}  1
${TEST_MODEL_VERSION_2}  2
${TEST_MODEL_NAME_1}     stub-model-4-1
${TEST_MODEL_NAME_2}     stub-model-4-2

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.grafana.Grafana
Library             legion.robot.libraries.model.Model
Library             Collections
Suite Setup         Run keywords  Choose cluster context    ${CLUSTER_NAME}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  \${TEST_MODEL_IMAGE_1}  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  \${TEST_MODEL_IMAGE_2}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_1}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_2}
Suite Teardown      Run keywords  Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  AND
...                 Remove File  ${LOCAL_CONFIG}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}
Test Teardown       Run Keywords
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_1}    AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_2}
Force Tags          edi  cli  enclave  multi_versions

*** Test Cases ***
Check EDI deploy 2 models with different versions but the same id
    [Setup]         NONE
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME_1} --image ${TEST_MODEL_IMAGE_1}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Check model started             ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION_1}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_1}'
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME_2} --image ${TEST_MODEL_IMAGE_2}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Check model started             ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION_2}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_2}'

Check EDI undeploy 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_NAME_1}
                    Should contain                  ${resp.stdout}          ${TEST_MODEL_NAME_2}

Check EDI undeploy all model instances by version
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME_1} --replicas 2
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_1}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_2}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_NAME_1}  DeploymentCreated   2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_NAME_2}  DeploymentCreated   1

    ${resp}=   Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_NAME_1}
                    Should contain                  ${resp.stdout}          ${TEST_MODEL_NAME_2}

    ${resp}=   Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_2}
                    Should Be Equal     ${resp.rc}         ${0}

Check EDI undeploy 1 of 2 models without version
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_NAME_1}
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_NAME_2}

Check EDI scale up 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME_1} --replicas 2
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_1}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_2}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_NAME_1}  DeploymentCreated   2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_NAME_2}  DeploymentCreated   1

Check EDI scale down 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME_1} --replicas 2
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_1}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_2}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_NAME_1}  DeploymentCreated   2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_NAME_2}  DeploymentCreated   1

    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME_1} --replicas 1
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_1}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_NAME_2}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_NAME_1}  DeploymentCreated   1
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_NAME_2}  DeploymentCreated   1

Check default model urls
    [Setup]  NONE
    [Tags]  apps
    ${edge}=             Build enclave EDGE URL     ${MODEL_TEST_ENCLAVE}
    Get token from EDI   ${TEST_MODEL_ID}   ${TEST_MODEL_VERSION_1}

    Run EDI deploy and check model started  ${TEST_MODEL_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}

    Get token from EDI   ${TEST_MODEL_ID}   ${TEST_MODEL_VERSION_1}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}

    Run EDI deploy and check model started  ${TEST_MODEL_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}

    Get token from EDI   ${TEST_MODEL_ID}   ${TEST_MODEL_VERSION_2}
    Run Keyword And Expect Error  *Returned wrong status code: 400*  Get model info  ${edge}  ${TOKEN}  ${TEST_MODEL_ID}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}
    Get token from EDI   ${TEST_MODEL_ID}   ${TEST_MODEL_VERSION_1}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}