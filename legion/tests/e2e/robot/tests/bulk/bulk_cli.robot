*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}         legion/config_bulk_cli
${CONN_1_ID}            bulk-test-conn-1
${CONN_2_ID}            bulk-test-conn-2
${TI_1_ID}              bulk-test-ti-1
${TI_2_ID}              bulk-test-ti-2
${PI_1_ID}              bulk-test-pi-1
${TRAINING_1_NAME}      bulk-test-mt-1

*** Settings ***
Documentation       Legion's EDI operational check for bulk operations (with multiple resources)
Test Timeout        20 minutes
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  bulk
Suite Setup         Run keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Run keywords  Cleanup resources  AND
...                               Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose conn delete --id ${CONN_1_ID} --ignore-not-found
    StrictShell  legionctl --verbose conn delete --id ${CONN_2_ID} --ignore-not-found
    StrictShell  legionctl --verbose ti delete --id ${TI_1_ID} --ignore-not-found
    StrictShell  legionctl --verbose ti delete --id ${TI_2_ID} --ignore-not-found
    StrictShell  legionctl --verbose pi delete --id ${PI_1_ID} --ignore-not-found
    StrictShell  legionctl --verbose train delete --id ${TRAINING_1_NAME} --ignore-not-found

Check toolchain integration
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose ti get --id ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check toolchain integration not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose ti get --id ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  "${name}" not found

Check packaging integration
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose pi get --id ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check packaging integration not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose pi get --id ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  "${name}" not found

Check connection
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose conn get --id ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check connection not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose conn get --id ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  not found

Apply bulk file and check counters
    [Arguments]  ${file}  ${created}  ${changed}  ${deleted}
    ${res}=  Shell  legionctl --verbose bulk apply ${RES_DIR}/${file}
             Should be equal  ${res.rc}      ${0}
             Run Keyword If   ${created} > 0  Should contain   ${res.stdout}  created resources: ${created}
             Run Keyword If   ${changed} > 0  Should contain   ${res.stdout}  changed resources: ${changed}
             Run Keyword If   ${deleted} > 0  Should contain   ${res.stdout}  deleted resources: ${deleted}

Apply bulk file and check errors
    [Arguments]  ${file}  ${expected_error_message}
    ${res}=  Shell  legionctl --verbose bulk apply ${RES_DIR}/${file}
             Should not be equal      ${res.rc}      ${0}
             Should contain       ${res.stdout}  ${expected_error_message}

Apply bulk file and check parse errors
    [Arguments]  ${file}  ${expected_error_message}
    ${res}=  Shell  legionctl --verbose bulk apply ${RES_DIR}/${file}
             Should not be equal      ${res.rc}      ${0}
             Should contain       ${res.stderr}  ${expected_error_message}

Remove bulk file and check counters
    [Arguments]  ${file}  ${created}  ${changed}  ${deleted}
    ${res}=  Shell  legionctl --verbose bulk delete ${RES_DIR}/${file}
             Should be equal  ${res.rc}      ${0}
             Run Keyword If   ${created} > 0  Should contain   ${res.stdout}  created resources: ${created}
             Run Keyword If   ${changed} > 0  Should contain   ${res.stdout}  changed resources: ${changed}
             Run Keyword If   ${deleted} > 0  Should contain   ${res.stdout}  removed resources: ${deleted}

Template. Apply good profile, check resources and remove on teardown
    [Arguments]  ${file}
    [Teardown]  Cleanup resources
    Check connection not exist               ${CONN_1_ID}
    Check connection not exist               ${CONN_2_ID}
    Check toolchain integration not exist    ${TI_1_ID}
    Check packaging integration not exist    ${PI_1_ID}
    Apply bulk file and check counters     ${file}  4  0  0
    Check connection               ${CONN_1_ID}
    Check connection               ${CONN_2_ID}
    Check toolchain integration    ${TI_1_ID}
    Check packaging integration    ${PI_1_ID}
    Remove bulk file and check counters    ${file}  0  0  4
    Check connection not exist               ${CONN_1_ID}
    Check connection not exist               ${CONN_2_ID}
    Check toolchain integration not exist    ${TI_1_ID}
    Check packaging integration not exist    ${PI_1_ID}

*** Test Cases ***
Apply good profile, check resources and remove on teardown
    [Documentation]  Apply good profile, validate and remove entities on end
    [Teardown]  Cleanup resources
    [Template]  Template. Apply good profile, check resources and remove on teardown
    file=correct.legion.yaml
    file=correct.legion.json

Apply changes on a good profile, remove on teardown
    [Documentation]  Apply changes on a good profile, validate resources, remove on teardown
    [Teardown]  Cleanup resources
    Check connection not exist               ${CONN_1_ID}
    Check connection not exist               ${CONN_2_ID}
    Check toolchain integration not exist    ${TI_1_ID}
    Check toolchain integration not exist    ${TI_2_ID}
    Check packaging integration not exist    ${PI_1_ID}
    Apply bulk file and check counters     correct.legion.yaml     4  0  0
    Check connection                         ${CONN_1_ID}
    Check connection                         ${CONN_2_ID}
    Check toolchain integration              ${TI_1_ID}
    Check toolchain integration not exist    ${TI_2_ID}
    Check packaging integration              ${PI_1_ID}
    Apply bulk file and check counters     correct.legion.yaml     0  4  0
    Check connection                         ${CONN_1_ID}
    Check connection                         ${CONN_2_ID}
    Check toolchain integration              ${TI_1_ID}
    Check toolchain integration not exist    ${TI_2_ID}
    Check packaging integration              ${PI_1_ID}
    Apply bulk file and check counters     correct-v2.legion.yaml  1  4  0
    Check connection             ${CONN_1_ID}
    Check connection             ${CONN_2_ID}
    Check toolchain integration  ${TI_1_ID}
    Check toolchain integration  ${TI_2_ID}
    Check packaging integration  ${PI_1_ID}
    Remove bulk file and check counters    correct-v2.legion.yaml  0  0  5
    Check connection not exist               ${CONN_1_ID}
    Check connection not exist               ${CONN_2_ID}
    Check toolchain integration not exist    ${TI_1_ID}
    Check toolchain integration not exist    ${TI_2_ID}
    Check packaging integration not exist    ${PI_1_ID}

Try to apply profile with incorrect order
    [Documentation]  Try to apply profile with resources in incorrect order
    [Teardown]  Cleanup resources
    Apply bulk file and check errors  incorrect-order.legion.yaml  not found

Try to apply profile with syntax error
    [Documentation]  Try to apply profile with resources in incorrect order
    [Teardown]  Cleanup resources
    Apply bulk file and check parse errors  corrupted.legion.yaml  is not valid JSON or YAML file

Try to apply profile with wrong kind
    [Documentation]  Try to apply profile with resources with wong kind
    [Teardown]  Cleanup resources
    Apply bulk file and check parse errors  wrong_kind.legion.yaml  Unknown kind of object
