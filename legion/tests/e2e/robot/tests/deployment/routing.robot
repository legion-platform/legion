*** Variables ***
${RES_DIR}                  ${CURDIR}/resources
${LOCAL_CONFIG}             legion/config_deployment_route
${MD_COUNTER_MODEL_1}       counter-model-route-1
${MD_COUNTER_MODEL_2}       counter-model-route-2
${MD_FAIL_MODEL}            fail-model-route
${TEST_MR_NAME}             test-route
${TEST_MR_URL_PREFIX}       /test-route/url

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Library             Collections
Suite Setup         Run keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources  AND
...                 Run EDI deploy from model packaging and check model started  ${MP_COUNTER_MODEL}   ${MD_COUNTER_MODEL_1}   ${RES_DIR}/min-replicas-0.deployment.legion.yaml  AND
...                 Run EDI deploy from model packaging and check model started  ${MP_COUNTER_MODEL}   ${MD_COUNTER_MODEL_2}   ${RES_DIR}/min-replicas-0.deployment.legion.yaml  AND
...                 Run EDI deploy from model packaging and check model started  ${MP_FAIL_MODEL}      ${MD_FAIL_MODEL}        ${RES_DIR}/min-replicas-0.deployment.legion.yaml
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}
Test Teardown       Cleanup routes
Force Tags          deployment  edi  cli  route

*** Keywords ***
Cleanup routes
    [Documentation]  Clean up all test routes
    StrictShell  legionctl --verbose route delete --id ${TEST_MR_NAME} --ignore-not-found

Cleanup deployments
    [Documentation]  Clean up all test deployments
    StrictShell  legionctl --verbose dep delete --id ${MD_COUNTER_MODEL_1} --ignore-not-found
    StrictShell  legionctl --verbose dep delete --id ${MD_COUNTER_MODEL_2} --ignore-not-found
    StrictShell  legionctl --verbose dep delete --id ${MD_FAIL_MODEL} --ignore-not-found

Cleanup resources
    [Documentation]  Clean up all test resources
    Cleanup routes
    Cleanup deployments

Expect number of replicas
    [Arguments]  ${md_name}  ${expected_number_of_replicas}
    ${res}=  StrictShell  legionctl dep get --id ${md_name} -o jsonpath='[*].status.replicas'

    should be equal as integers  ${expected_number_of_replicas}  ${res.stdout}

Check mr
    [Arguments]  ${url}
    ${res}=  Shell  legionctl --verbose route get --id ${TEST_MR_NAME}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stdout}  ${TEST_MR_NAME}
             Should contain   ${res.stdout}  ${url}
             Should contain   ${res.stdout}  stub-model-6-5-1=100

Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose route create -f ${LEGION_ENTITIES_DIR}/mr/${create_file}
             Should be equal  ${res.rc}  ${0}

    Check route  ${EDGE_URL}${TEST_MR_URL_PREFIX}/original

    ${res}=  Shell  legionctl --verbose route edit -f ${LEGION_ENTITIES_DIR}/mr/${edit_file}
             Should be equal  ${res.rc}  ${0}

    Check route  ${EDGE_URL}${TEST_MR_URL_PREFIX}/changed

    ${res}=  Shell  legionctl --verbose route delete -f ${LEGION_ENTITIES_DIR}/mr/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose route get ${TEST_MR_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose route ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose route ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Provide name of a Model Route or path to a file

Check model counter
    [Arguments]  ${md_name}
        ${res}=  Wait Until Keyword Succeeds  2m  10 sec  Shell  legionctl --verbose model invoke --md ${md_name} --json-file ${RES_DIR}/simple-model.request.json
                 Should be equal  ${res.rc}  ${0}
                 ${RESPONSE}=  evaluate  json.loads('''${res.stdout}''')  json
                 should be true  ${RESPONSE["prediction"][0][0]} > 0

*** Test Cases ***
Getting of nonexistent Route by name
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose route get --id ${TEST_MR_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Basic routing
    [Documentation]  Basic route
    StrictShell  legionctl --verbose route create --id ${TEST_MR_NAME} -f ${RES_DIR}/test-50-50-counter.route.legion.yaml

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    Wait Until Keyword Succeeds  2m  10 sec  StrictShell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}

    Check model counter  ${MD_COUNTER_MODEL_1}
    Check model counter  ${MD_COUNTER_MODEL_2}

Basic mirroring
    [Documentation]  Route with mirroring
    StrictShell  legionctl --verbose route create --id ${TEST_MR_NAME} -f ${RES_DIR}/test-counter-mirror.route.legion.yaml

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    Wait Until Keyword Succeeds  2m  10 sec  StrictShell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}

    Check model counter  ${MD_COUNTER_MODEL_1}
    Check model counter  ${MD_COUNTER_MODEL_2}

Mirror to broken model
    [Documentation]  Mirror traffic to broken model
    StrictShell  legionctl --verbose route create --id ${TEST_MR_NAME} -f ${RES_DIR}/test-fail-mirror.route.legion.yaml

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    Wait Until Keyword Succeeds  2m  10 sec  StrictShell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}

    Check model counter  ${MD_COUNTER_MODEL_1}

File with entitiy not found
    [Documentation]  Invoke Model Route commands with not existed file
    [Template]  File not found
    command=create
    command=edit
    command=delete

Scaledown to zero pods
    [Tags]  kek
    [Documentation]  Wait until model scales down to zero pods
    Wait Until Keyword Succeeds  4m  5 sec  Expect number of replicas  ${MD_COUNTER_MODEL_1}  0

    Check model counter  ${MD_COUNTER_MODEL_1}

    Wait Until Keyword Succeeds  2m  5 sec  Expect number of replicas  ${MD_COUNTER_MODEL_1}  1
