*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        5 minutes
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Library             Process
Suite Setup         Choose cluster context    ${CLUSTER_NAME}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}   AND
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
Test Teardown       Run Keywords
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}   ${TEST_MODEL_IMAGE_1}    AND
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}   ${TEST_MODEL_IMAGE_2}

*** Test Cases ***
Check EDI availability in all enclaves
    [Setup]         NONE
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave   multi_versions
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  ${edi_state} =           Run EDI inspect  ${enclave}
    \  Log                      ${edi_state}
    \  Should Be Equal As Integers       ${edi_state.rc}   0
    [Teardown]      NONE

Check EDI deploy 2 models with different versions but the same id
    [Setup]         NONE
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                      ${resp}                 "model_version": "${TEST_MODEL_1_VERSION}"
    ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
                    Should contain                      ${resp}                 "model_version": "${TEST_MODEL_2_VERSION}"

Check EDI undeploy 1 of 2 models with different versions but the same id
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=        Run EDI undeploy with version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_IMAGE_1}
                    Should contain                  ${resp.stdout}          ${TEST_MODEL_IMAGE_2}

Check EDI undeploy all model instances by version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  1

    ${resp}=   Run EDI undeploy with version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should not contain              ${resp.stdout}          ${TEST_MODEL_1_VERSION}
                    Should contain                  ${resp.stdout}          ${TEST_MODEL_2_VERSION}

Check EDI undeploy 1 of 2 models without version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI undeploy without version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers        ${resp.rc}         2
                    Should contain                     ${resp.stderr}     Please specify version of model

Check EDI scale up 1 of 2 models with different versions but the same id
    [Tags]  edi  cli  enclave   multi_versions
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
    [Tags]  edi  cli  enclave   multi_versions
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
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   ${TEST_MODEL_1_VERSION}121
                    Should Be Equal As Integers     ${resp.rc}              2
                    Should contain                  ${resp.stderr}          No one model can be found

Check EDI scale up 1 of 2 models without version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=        Run EDI scale                   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2
                    Should Be Equal As Integers     ${resp.rc}              2
                    Should contain                  ${resp.stderr}          Please specify version of model

Check EDI model inspect by model id return 2 models
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_1}
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model version return 1 model
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers         ${resp.rc}          0
                    Should contain                      ${resp.stdout}      ${TEST_MODEL_IMAGE_1}
                    Should not contain                  ${resp.stdout}      ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model id and version return 1 model
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}      ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers                      ${resp.rc}         0
                    Should contain                                   ${resp.stdout}     ${TEST_MODEL_IMAGE_1}
                    Should not contain                               ${resp.stdout}     ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by invalid model id
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should be empty                 ${resp.stdout}

Check EDI model inspect by invalid model version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model version    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers         ${resp.rc}        0
                    Should be empty                     ${resp.stdout}

Check EDI model inspect by invalid model id and invalid version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test   ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers                      ${resp.rc}          0
                    Should be empty                                  ${resp.stdout}

Check EDI model inspect by invalid model id and valid version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}test   ${TEST_MODEL_1_VERSION}
                    Should Be Equal As Integers                      ${resp.rc}          0
                    Should be empty                                  ${resp.stdout}

Check EDI model inspect by valid model id and invalid version
    [Tags]  edi  cli  enclave   multi_versions
    ${resp}=   Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}test
                    Should Be Equal As Integers                      ${resp.rc}          0
                    Should be empty                                  ${resp.stdout}
