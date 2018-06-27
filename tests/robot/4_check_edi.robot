*** Settings ***
Documentation       Legion's EDI operational check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ../../deploy/profiles/
Library             legion_test.robot.Utils
Library             Collections
Test Setup          Run Keywords
...                 Choose cluster context    ${CLUSTER_NAME}   AND
...                 Run EDI deploy and check model started      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION} AND
...                 Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}

Test Teardown       Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}

*** Test Cases ***
Check EDI availability in all enclaves
    [Setup]     Choose cluster context    ${CLUSTER_NAME}
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  ${edi_state}=    Run EDI inspect  ${enclave}
    \  Should Be Equal As Integers       ${edi_state.rc}         0
    \  Should Contain                    ${edi_state.output}     Model ID|Image|Version|Ready|Scale|Errors
    [Teardown]    NONE

Check EDI deploy procedure
    [Setup]     Choose cluster context    ${CLUSTER_NAME}
    [Documentation]  Try to deploy dummy model trough EDI console
    [Tags]  edi  cli  enclave
    Run EDI deploy and check model started              ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
    Run EDI inspect and verify info from edi            ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}

Check EDI undeploy procedure
    [Documentation]  Try to undeploy dummy valid model trough EDI console
    [Tags]  edi  cli  enclave
    Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
    [Teardown]    NONE

Check EDI invalid deploy procedure
    [Setup]     NONE
    [Documentation]  Try to deploy dummy invalid model trough EDI console
    [Tags]  edi  cli  enclave

    ${edi_state}=                Run EDI deploy   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}test
    Should Be Equal As Integers  ${edi_state.rc}        1
    Should Contain               ${edi_state.output}    Cannot find model deployment after deploy for image ${TEST_MODEL_IMAGE_1}test
    [Teardown]    NONE

Check EDI invalid undeploy procedure
    [Documentation]  Try to undeploy invalid dummy model trough EDI console
    [Tags]  edi  cli  enclave

    ${edi_state}=                Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}test
    Should Be Equal As Integers  ${edi_state.rc}        1
    Should Contain               ${edi_state.output}    Cannot find any deployment
    [Teardown]    NONE

Check EDI scale procedure
    [Documentation]  Try to deploy, scale and undeploy dummy model trough EDI console
    [Tags]  edi  cli  enclave
    Run EDI scale model without version and check   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    2

Check EDI invalid scale procedure - invalid model id
    [Documentation]  Try to scale invalid dummy model trough EDI console
    [Tags]  edi  cli  enclave

    ${scale_result} =            Run EDI scale   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}test   1
    Should Be Equal As Integers  ${scale_result.rc}     1
    Should contain               ${scale_result.output} No one model can be found