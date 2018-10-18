*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Choose cluster context    ${CLUSTER_NAME}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}    ${TEST_MODEL_1_VERSION}   AND
...                 Run EDI deploy and check model started          ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}    ${TEST_MODEL_2_VERSION}
Test Teardown       Run Keywords
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}   ${TEST_MODEL_IMAGE_1}    AND
...                 Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}   ${TEST_MODEL_IMAGE_2}

*** Test Cases ***
Check EDI undeploy all versioned model instances by id=*
    [Documentation]  Try to undeploy all models by id=* through EDI console
    [Tags]  edi  cli  enclave  multi_versions
    ${resp}=        Run EDI undeploy without version    ${MODEL_TEST_ENCLAVE}    '*'
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should be empty                 ${resp.stdout}

Check EDI undeploy all versioned model instances by versions=*
    [Documentation]  Try to undeploy all models by versions=* through EDI console
    [Tags]  edi  cli  enclave  multi_versions
   ${resp}=         Run EDI undeploy with version   ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    '*'
                    Should Be Equal As Integers     ${resp.rc}         0
    ${resp}=        Run EDI inspect by model id     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should be empty                 ${resp.stdout}

Check EDI scale up all instances for 2 models(diff versions) by versions=*
    [Documentation]  Try to scale up 2 models with different versions but the same id by all versions through EDI console
    [Tags]  edi  cli  enclave  multi_versions
    ${resp}=        Run EDI scale with version      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    2   '*'
                    Should Be Equal As Integers     ${resp.rc}              0
    ${resp}=        Run EDI inspect with parse by model id       ${MODEL_TEST_ENCLAVE}      ${TEST_MODEL_ID}
    ${model_1}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_1_VERSION}
                    Log                             ${model_1}
    ${model_2}=     Find model information in edi   ${resp}      ${TEST_MODEL_ID}   ${TEST_MODEL_2_VERSION}
                    Log                             ${model_2}
                    Verify model info from edi      ${model_1}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_1_VERSION}  2
                    Verify model info from edi      ${model_2}   ${TEST_MODEL_ID}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_2_VERSION}  2

Check EDI scale up all instances for 2 models(diff versions) by id=*
    [Documentation]  Try to scale up 2 models with different versions but the same id by all ids through EDI console
    [Tags]  edi  cli  enclave  multi_versions
    ${resp}=        Run EDI scale                   ${MODEL_TEST_ENCLAVE}   '*'    2
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
    [Tags]  edi  cli  enclave  multi_versions
    ${resp}=        Run EDI inspect by model id    ${MODEL_TEST_ENCLAVE}   '*'
                    Should Be Equal As Integers    ${resp.rc}         0
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_IMAGE_1}
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_IMAGE_2}

Check EDI model inspect by model version=* return all models
    [Documentation]  Try to inspect 2 models by all versions through EDI console
    [Tags]  edi  cli  enclave  multi_versions
    ${resp}=        Run EDI inspect by model id and model version    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_ID}    '*'
                    Should Be Equal As Integers    ${resp.rc}        0
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_IMAGE_1}
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_IMAGE_2}