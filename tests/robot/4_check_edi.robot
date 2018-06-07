*** Settings ***
Documentation       Legion's EDI operational check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ../../deploy/profiles/
Library             legion_test.robot.Utils
Library             Collections
Test Setup          Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Check EDI availability in all enclaves
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  edi  cli  enclave
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  ${edi_state} =           Run EDI inspect  ${enclave}
    \  Log                      ${edi_state}
    \  Should not contain       ${edi_state}   legionctl: error
    \  Should not contain       ${edi_state}   Exception

Check EDI deploy and undeploy procedure
    [Documentation]  Try to deploy and undeploy dummy model trough EDI console
    [Tags]  edi  cli  enclave
    Run EDI deploy                                     ${MODEL_TEST_ENCLAVE}         ${TEST_MODEL_IMAGE}
    Sleep            5

    ${edi_state} =      Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${target_model} =   Find model information in edi  ${edi_state}                  ${TEST_MODEL_ID}
    Log  ${edi_state}
    Log  ${target_model}

    Should Be Equal  ${target_model[0]}    ${TEST_MODEL_ID}             invalid model id
    Should Be Equal  ${target_model[1]}    ${TEST_MODEL_IMAGE}          invalid model image
    Should Be Equal  ${target_model[2]}    ${TEST_MODEL_VERSION}        invalid model version
    Should Be Equal  ${target_model[3]}    1                            invalid actual scales
    Should Be Equal  ${target_model[4]}    1                            invalid desired scale
    Should Be Empty  ${target_model[5]}                                 got some errors ${target_model[5]}

    Run EDI undeploy without version                   ${MODEL_TEST_ENCLAVE}         ${TEST_MODEL_ID}

    ${edi_state} =   Run EDI inspect                   ${MODEL_TEST_ENCLAVE}
    Log  ${edi_state}
    Should not contain                                 ${edi_state}                  ${TEST_MODEL_ID}

Check EDI scale procedure
    [Documentation]  Try to deploy, scale and undeploy dummy model trough EDI console
    [Tags]  edi  cli  enclave
    Run EDI deploy                                     ${MODEL_TEST_ENCLAVE}         ${TEST_MODEL_IMAGE}
    Sleep            5

    ${edi_state} =      Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${target_model} =   Find model information in edi  ${edi_state}                  ${TEST_MODEL_ID}
    Log  ${edi_state}
    Log  ${target_model}

    Should Be Equal  ${target_model[0]}    ${TEST_MODEL_ID}             invalid model id
    Should Be Equal  ${target_model[1]}    ${TEST_MODEL_IMAGE}          invalid model image
    Should Be Equal  ${target_model[2]}    ${TEST_MODEL_VERSION}        invalid model version
    Should Be Equal  ${target_model[3]}    1                            invalid actual scales
    Should Be Equal  ${target_model[4]}    1                            invalid desired scale
    Should Be Empty  ${target_model[5]}                                 got some errors ${target_model[5]}

    ${scale_result} =  Run EDI scale       ${MODEL_TEST_ENCLAVE}        ${TEST_MODEL_ID}   2
    Should not contain                     ${scale_result}              error
    Sleep            10

    ${edi_state} =      Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${target_model} =   Find model information in edi  ${edi_state}                  ${TEST_MODEL_ID}
    Log  ${edi_state}
    Log  ${target_model}

    Should Be Equal  ${target_model[0]}    ${TEST_MODEL_ID}             invalid model id
    Should Be Equal  ${target_model[1]}    ${TEST_MODEL_IMAGE}          invalid model image
    Should Be Equal  ${target_model[2]}    ${TEST_MODEL_VERSION}        invalid model version
    Should Be Equal  ${target_model[3]}    2                            invalid actual scales
    Should Be Equal  ${target_model[4]}    2                            invalid desired scale
    Should Be Empty  ${target_model[5]}                                 got some errors ${target_model[5]}

    Run EDI undeploy without version                   ${MODEL_TEST_ENCLAVE}         ${TEST_MODEL_ID}

    ${edi_state} =   Run EDI inspect                   ${MODEL_TEST_ENCLAVE}
    Log  ${edi_state}
    Should not contain                                 ${edi_state}                  ${TEST_MODEL_ID}
