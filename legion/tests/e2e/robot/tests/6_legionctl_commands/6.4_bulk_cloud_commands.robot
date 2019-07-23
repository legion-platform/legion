*** Variables ***
${LOCAL_CONFIG}         legion/config_6_4
${VCS_1_NAME}           bulk-test-vcs-1
${VCS_2_NAME}           bulk-test-vcs-2
${TRAINING_1_NAME}      bulk-test-mt-1
${TRAINING_2_NAME}      bulk-test-mt-2
${TRAINING_3_NAME}      bulk-test-mt-3
${DEPLOY_1_NAME}        bulk-test-md-1
${DEPLOY_2_NAME}        bulk-test-md-2

*** Settings ***
Documentation       Legion's EDI operational check for bulk operations (with multiple resources)
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps  mt  md  vcs  bulk
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    Shell  legionctl --verbose vcs delete ${VCS_1_NAME}
    Shell  legionctl --verbose vcs delete ${VCS_2_NAME}
    Shell  legionctl --verbose mt delete ${TRAINING_1_NAME}
    Shell  legionctl --verbose mt delete ${TRAINING_2_NAME}
    Shell  legionctl --verbose mt delete ${TRAINING_3_NAME}
    Shell  legionctl --verbose md delete ${DEPLOY_1_NAME}
    Shell  legionctl --verbose md delete ${DEPLOY_2_NAME}

Check model training
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose mt get ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check model training not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose mt get ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  "${name}" not found

Check model deployment
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose md get ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check model deployment not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose md get ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  "${name}" not found

Check VCS
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose vcs get ${name}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stderr}  ${name}

Check VCS not exist
    [Arguments]  ${name}
    ${res}=  Shell  legionctl --verbose vcs get ${name}
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  "${name}" not found

Apply bulk file and check counters
    [Arguments]  ${file}  ${created}  ${changed}  ${deleted}
    ${res}=  Shell  legionctl --verbose cloud apply ${LEGION_ENTITIES_DIR}/bulk/${file}
             Should be equal  ${res.rc}      ${0}
             Run Keyword If   ${created} > 0  Should contain   ${res.stdout}  created resources: ${created}
             Run Keyword If   ${changed} > 0  Should contain   ${res.stdout}  changed resources: ${changed}
             Run Keyword If   ${deleted} > 0  Should contain   ${res.stdout}  deleted resources: ${deleted}

Apply bulk file and check errors
    [Arguments]  ${file}  ${expected_error_message}
    ${res}=  Shell  legionctl --verbose cloud apply ${LEGION_ENTITIES_DIR}/bulk/${file}
             Should be equal      ${res.rc}      ${1}
             Should contain       ${res.stdout}  ${expected_error_message}

Apply bulk file and check parse errors
    [Arguments]  ${file}  ${expected_error_message}
    ${res}=  Shell  legionctl --verbose cloud apply ${LEGION_ENTITIES_DIR}/bulk/${file}
             Should be equal      ${res.rc}      ${2}
             Should contain       ${res.stderr}  ${expected_error_message}

Remove bulk file
    [Arguments]  ${file}
    ${res}=  Shell  legionctl --verbose cloud remove ${LEGION_ENTITIES_DIR}/bulk/${file}

Remove bulk file and check counters
    [Arguments]  ${file}  ${created}  ${changed}  ${deleted}
    ${res}=  Shell  legionctl --verbose cloud remove ${LEGION_ENTITIES_DIR}/bulk/${file}
             Should be equal  ${res.rc}      ${0}
             Run Keyword If   ${created} > 0  Should contain   ${res.stdout}  created resources: ${created}
             Run Keyword If   ${changed} > 0  Should contain   ${res.stdout}  changed resources: ${changed}
             Run Keyword If   ${deleted} > 0  Should contain   ${res.stdout}  removed resources: ${deleted}

Template. Apply good profile, check resources and remove on teardown
    [Arguments]  ${file}
    [Teardown]  Remove bulk file      ${file}
    Check VCS not exist               ${VCS_1_NAME}
    Check model training not exist    ${TRAINING_1_NAME}
    Check model training not exist    ${TRAINING_2_NAME}
    Check model training not exist    ${TRAINING_3_NAME}
    Wait Until Keyword Succeeds  3m  5 sec  Check model deployment not exist  ${DEPLOY_1_NAME}
    Apply bulk file and check counters     ${file}  4  0  0
    Check VCS               ${VCS_1_NAME}
    Check model training    ${TRAINING_1_NAME}
    Check model training    ${TRAINING_2_NAME}
    Check model deployment  ${DEPLOY_1_NAME}
    Check model training not exist    ${TRAINING_3_NAME}
    Remove bulk file        ${file}

*** Test Cases ***
Apply good profile, check resources and remove on teardown
    [Documentation]  Apply good profile, validate and remove entities on end
    [Template]  Template. Apply good profile, check resources and remove on teardown
    file=correct.legion.yaml
    file=correct.json

Apply changes on a good profile, remove on teardown
    [Documentation]  Apply changes on a good profile, validate resources, remove on teardown
    [Teardown]  Remove bulk file      correct-v2.legion.yaml
    Check VCS not exist               ${VCS_1_NAME}
    Check model training not exist    ${TRAINING_1_NAME}
    Check model training not exist    ${TRAINING_2_NAME}
    Check model training not exist    ${TRAINING_3_NAME}
    Wait Until Keyword Succeeds  3m  5 sec  Check model deployment not exist  ${DEPLOY_1_NAME}
    Apply bulk file and check counters     correct.legion.yaml     4  0  0
    Check VCS               ${VCS_1_NAME}
    Check model training    ${TRAINING_1_NAME}
    Check model training    ${TRAINING_2_NAME}
    Check model deployment  ${DEPLOY_1_NAME}
    Check model training not exist    ${TRAINING_3_NAME}
    Apply bulk file and check counters     correct.legion.yaml     0  4  0
    Check VCS               ${VCS_1_NAME}
    Check model training    ${TRAINING_1_NAME}
    Check model training    ${TRAINING_2_NAME}
    Check model deployment  ${DEPLOY_1_NAME}
    Check model training not exist    ${TRAINING_3_NAME}
    Apply bulk file and check counters     correct-v2.legion.yaml  1  4  0
    Check VCS               ${VCS_1_NAME}
    Check model training    ${TRAINING_1_NAME}
    Check model training    ${TRAINING_2_NAME}
    Check model deployment  ${DEPLOY_1_NAME}
    Check model training    ${TRAINING_3_NAME}
    Remove bulk file and check counters    correct-v2.legion.yaml  0  0  5

Try to apply profile with incorrect order
    [Documentation]  Try to apply profile with resources in incorrect order
    [Teardown]  Remove bulk file      incorrect-order.legion.yaml
    Apply bulk file and check errors  incorrect-order.legion.yaml  "${VCS_2_NAME}" not found

Try to apply profile with syntax error
    [Documentation]  Try to apply profile with resources in incorrect order
    [Teardown]  Remove bulk file      corrupted.legion.yaml
    Apply bulk file and check parse errors  corrupted.legion.yaml  Invalid Legion resource in file