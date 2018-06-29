*** Settings ***
Documentation       Legion's EDI operational check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ../../deploy/profiles/
Library             legion_test.robot.Utils
Library             Collections
Test Setup          Run Keywords
...                 Choose cluster context    ${CLUSTER_NAME}   AND
...                 Run EDI deploy and check model started      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}  AND
...                 Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}  AND
...                 Run EDI deploy and check model started      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}  AND
...                 Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}  AND
...                 Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}  AND
...                 Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
Test Teardown       Run Keywords
...                 Run EDI undeploy by model version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}   AND
...                 Run EDI undeploy by model version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}

*** Test Cases ***
Check EDI availability in all enclaves
    [Setup]     Choose cluster context    ${CLUSTER_NAME}
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  ${edi_state} =           Run EDI inspect  ${enclave}
    \  Log                      ${edi_state}
    \  Should Be Equal As Integers      ${edi_state.rc}   0
    [Teardown]    NONE

Check EDI deploy 2 models with different versions but the same id
    [Setup]     Choose cluster context    ${CLUSTER_NAME}
    [Tags]  edi  cli  enclave
    Run EDI deploy and check model started      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
    Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
    Run EDI deploy and check model started      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
    Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
    Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}  ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}
    Run EDI inspect and verify info from edi    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}  ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}

Check EDI scale up 1 of 2 models with different versions but the same id
    [Tags]  edi  cli  enclave
    # scale one model
    Run EDI scale model with version and check  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    2     ${TEST_MODEL_1_VERSION}

Check EDI scale down 1 of 2 models with different versions but the same id
    [Tags]  edi  cli  enclave
    # scale one model up
    Run EDI scale model with version and check  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    2     ${TEST_MODEL_1_VERSION}
    # scale one model down
    Run EDI scale model with version and check  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    1     ${TEST_MODEL_1_VERSION}

Check EDI scale up 1 of 2 models with different versions but the same id - invalid version
    [Tags]  edi  cli  enclave
    # try to scale one model with invalid version
    Run EDI scale model with version and check error  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    2     ${TEST_MODEL_1_VERSION}121  No one model can be found

Check EDI scale up 1 of 2 models with different versions but the same id - without version
    [Tags]  edi  cli  enclave
    # try to scale one model with invalid version
    Run EDI scale model without version and check error  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    2     Please specify version of model

Check EDI undeploy 1 of 2 models with different versions but the same id
    [Tags]  edi  cli  enclave
    # scale one model up
    Run EDI scale model with version and check  ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    2     ${TEST_MODEL_1_VERSION}

Check EDI undeploy 1 of 2 models with different versions but the same id - invalid version
    [Tags]  edi  cli  enclave
    # scale one model up
    Run EDI scale model with version and check          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    2     ${TEST_MODEL_1_VERSION}
    # try to undeploy with invalid model version
    Run EDI undeploy by model version and check error   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}    Cannot find any deployment

Check EDI undeploy 1 of 2 models with different versions but the same id - without version
    [Tags]  edi  cli  enclave
       # try to undeploy with invalid model version
    Run EDI undeploy model without version and check error ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   Please specify version of model




