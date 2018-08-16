*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        5 minutes
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Library             Process
Suite Setup         Choose cluster context                              ${CLUSTER_NAME}
Test Setup          Run EDI deploy and check model started              ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
Test Teardown       Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}

*** Test Cases ***
Check EDI availability in all enclaves
    [Setup]         NONE
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave   one_version
    :FOR    ${enclave}      IN                            @{ENCLAVES}
    \       ${edi_state}=   Run EDI inspect               ${enclave}
    \                       Should Be Equal As Integers   ${edi_state.rc}     0
    [Teardown]                    NONE

Check EDI deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${response}=    Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                      ${response}             "model_version": "${TEST_MODEL_1_VERSION}"

Check EDI deploy with scale to 0
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   0
                    Should Be Equal As Integers    ${resp.rc}         2
                    Should contain                 ${resp.stderr}     Invalid scale parameter: should be greater then 0

Check EDI deploy with scale to 1
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   1
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                 ${response}             "model_version": "${TEST_MODEL_1_VERSION}"

    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_ID}    ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}   1

Check EDI deploy with scale to 2
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   2
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                 ${response}             "model_version": "${TEST_MODEL_1_VERSION}"

    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_ID}    ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}   2

Check EDI invalid model name deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy dummy invalid model name through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}test
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Can't get image labels for  ${TEST_MODEL_IMAGE_1}test

Check EDI double deploy procedure for the same model
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Documentation]  Try to deploy twice the same dummy model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers   ${resp.rc}         0
    ${response}=    Check model started           ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
                    Should contain                ${response}             "model_version": "${TEST_MODEL_1_VERSION}"
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Duplicating model id and version (id=${TEST_MODEL_ID}, version=${TEST_MODEL_1_VERSION})

Check EDI undeploy procedure
    [Documentation]  Try to undeploy dummy valid model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI undeploy without version    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Run EDI inspect                     ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers         ${resp.rc}         0
                    Should not contain                  ${resp.stdout}     ${model_id}

Check EDI scale up procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    2
                    Should Be Equal As Integers    ${resp.rc}           0
                    Sleep                          10  # because no way to control explicitly scaling the model inside
    # TODO remove sleep
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_ID}    ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}   2

Check EDI scale down procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    2
                    Should Be Equal As Integers    ${resp.rc}          0
                    Sleep                          10
    # TODO remove sleep
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_ID}    ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}   2

    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    1
                    Should Be Equal As Integers    ${resp.rc}          0
                    Sleep                          10
    # TODO remove sleep
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_ID}    ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}   1

Check EDI scale to 0 procedure
    [Documentation]  Try to scale to 0 model through EDI console
    [Tags]  edi  cli  enclave one_version
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    0
                    Should Be Equal As Integers    ${resp.rc}          2
                    Should contain                 ${resp.stderr}      Invalid scale parameter: should be greater then 0

Check EDI invalid model id scale up procedure
    [Documentation]  Try to scale up dummy model with invalid name through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI scale                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}test   2
                    Should Be Equal As Integers  ${resp.rc}         2
                    Should contain               ${resp.stderr}     No one model can be found

Check EDI enclave inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should contain                 ${resp.stdout}      ${TEST_MODEL_ID}

Check EDI invalid enclave name inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}test
                    Should Be Equal As Integers    ${resp.rc}          2
                    Should contain                 ${resp.stderr}      ERROR - Failed to connect

Check EDI enclave inspect procedure without deployed model
    [Setup]         NONE
    [Documentation]  Try inspect through EDI console on empty enclave
    [Tags]  edi  cli  enclave   one_version
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should Not Contain             ${resp.stdout}      ${model_id}
    [Teardown]      NONE