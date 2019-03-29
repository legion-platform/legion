*** Variables ***
${LOCAL_CONFIG}  legion/config_4_0

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
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}   AND
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
Test Teardown       Run Keywords
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}   ${TEST_MODEL_IMAGE_1}    AND
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}   ${TEST_MODEL_IMAGE_2}    AND
...                 Remove File  ${LOCAL_CONFIG}
Force Tags          edi  cli  enclave  multi_versions

*** Test Cases ***
Check EDI deploy 2 models with different versions but the same id
    [Setup]         NONE
    [Tags]  apps
    ${resp}=        Run EDI deploy                  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Check model started             ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                  ${resp}                 "model_version": "${TEST_MODEL_1_VERSION}"
    ${resp}=        Run EDI deploy                  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Check model started             ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
                    Should contain                  ${resp}                 "model_version": "${TEST_MODEL_2_VERSION}"

Check EDI undeploy 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Run EDI undeploy with version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_IMAGE_1}
                    Should contain                  ${resp.stdout}          ${TEST_MODEL_IMAGE_2}

Check EDI undeploy all model instances by version
    [Tags]  apps
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  1

    ${resp}=   Run EDI undeploy with version        ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          |${TEST_MODEL_1_VERSION}
                    Should contain                  ${resp.stdout}          |${TEST_MODEL_2_VERSION}

    ${resp}=        Run EDI undeploy with version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0

Check EDI undeploy 1 of 2 models without version
    [Tags]  apps
    ${resp}=   Run EDI undeploy without version     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}         2
                    Should contain                  ${resp.stderr}     Please specify version of model

Check EDI scale up 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  1

Check EDI scale down 1 of 2 models with different versions but the same id
    [Tags]  apps
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  1

    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    1   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  1
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  1

Check EDI scale up 1 of 2 models by invalid version
    [Tags]  apps
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}121
                    Should Be Equal As Integers     ${resp.rc}              2
                    Should contain                  ${resp.stderr}          No one model can be found

Check EDI scale up 1 of 2 models without version
    [Tags]  apps
    ${resp}=        Run EDI scale                   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2
                    Should Be Equal As Integers     ${resp.rc}              2
                    Should contain                  ${resp.stderr}          Please specify version of model

Check EDI model inspect by model id return 2 models
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id          ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_1}
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model version return 1 model
    [Tags]  apps
    ${resp}=   Run EDI inspect by model version     ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_1}
                    Should not contain              ${resp.stdout}      ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model id and version return 1 model
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}      ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers                 ${resp.rc}         0
                    Should contain                              ${resp.stdout}     ${TEST_MODEL_IMAGE_1}
                    Should not contain                          ${resp.stdout}     ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by invalid model id
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id          ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should be empty                 ${resp.stdout}

Check EDI model inspect by invalid model version
    [Tags]  apps
    ${resp}=   Run EDI inspect by model version     ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers     ${resp.rc}        0
                    Should be empty                 ${resp.stdout}

Check EDI model inspect by invalid model id and invalid version
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test   ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI model inspect by invalid model id and valid version
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI model inspect by valid model id and invalid version
    [Tags]  apps
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI scale up all instances for 2 models(diff versions) by versions=*
    [Documentation]  Try to scale up 2 models with different versions but the same id by all versions through EDI console
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   '*'
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  2

Check EDI model inspect by model id=* return all models
    [Documentation]  Try to inspect 2 models by all ids through EDI console
    ${resp}=        Run EDI inspect by model id    ${MODEL_TEST_ENCLAVE}   '*'
                    Should Be Equal As Integers    ${resp.rc}         0
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_IMAGE_1}
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model version=* return all models
    [Documentation]  Try to inspect 2 models by all versions through EDI console
    ${resp}=        Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    '*'
                    Should Be Equal As Integers    ${resp.rc}        0
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_IMAGE_1}
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_IMAGE_2}

Check default model urls
    [Setup]  NONE
    [Tags]  apps
    ${edge}=             Build enclave EDGE URL     ${MODEL_TEST_ENCLAVE}
    Get token from EDI   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}

    ${resp}=        Run EDI deploy                  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Check model started             ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                  ${resp}                 "model_version": "${TEST_MODEL_1_VERSION}"

    Get token from EDI   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_1_VERSION}

    ${resp}=        Run EDI deploy                  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Check model started             ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}  ${TEST_MODEL_2_VERSION}
                    Should contain                  ${resp}                 "model_version": "${TEST_MODEL_2_VERSION}"

    Get token from EDI   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
    Run Keyword And Expect Error  *Returned wrong status code: 400*  Get model info  ${edge}  ${TOKEN}  ${TEST_MODEL_ID}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_2_VERSION}
    Get token from EDI   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
    Get model info       ${edge}  ${TOKEN}  ${TEST_MODEL_ID}  ${TEST_MODEL_1_VERSION}

Invoke two models
    [Documentation]  Check that config holds model jwts separately
    [Tags]  apps  kek
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_1_VERSION}
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_2_VERSION}
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl config set MODEL_SERVER_URL https://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_1_VERSION} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_2_VERSION} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42