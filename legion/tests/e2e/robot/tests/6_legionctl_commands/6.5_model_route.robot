*** Variables ***
${LOCAL_CONFIG}             legion/config_6_5
${TEST_MODEL_NAME}          6-5
${TEST_MODEL_VERSION_1}     1
${TEST_MODEL_VERSION_2}     2
${TEST_FAIL_MODEL_VERSION}  3
${TEST_MT_NAME_1}           stub-model-6-5-1
${TEST_MT_NAME_2}           stub-model-6-5-2
${TEST_FAIL_MT_NAME}        fail-model-6-5-3
${TEST_MD_NAME_1}           stub-model-6-5-1
${TEST_MD_NAME_2}           stub-model-6-5-2
${TEST_FAIL_MD_NAME}        fail-model-6-5-3
${TEST_MR_NAME}             stub-rote65
${TEST_MR_URL_PREFIX}       /test6-5/url
&{FAIL_ARGS}                --fail-threshold=1

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
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build model  ${TEST_MT_NAME_1}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_1}     \${TEST_MODEL_IMAGE_1}  entrypoint=counter.py  AND
...                 Build model  ${TEST_MT_NAME_2}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_2}     \${TEST_MODEL_IMAGE_2}  entrypoint=counter.py  AND
...                 Build model  ${TEST_FAIL_MT_NAME}  ${TEST_MODEL_NAME}  ${TEST_FAIL_MODEL_VERSION}  \${TEST_FAIL_MODEL_IMAGE}  counter.py  ${FAIL_ARGS}  AND
...                 Get token from EDI  ${TEST_MD_NAME_1}  AND
...                 Get token from EDI  ${TEST_MD_NAME_2}  AND
...                 Get token from EDI  ${TEST_FAIL_MD_NAME}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_1}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_2}  AND
...                 Run EDI undeploy model and check    ${TEST_FAIL_MD_NAME}
Suite Teardown      Run keywords  Delete model training  ${TEST_MT_NAME_1}  AND
...                 Delete model training  ${TEST_MT_NAME_2}  AND
...                 Delete model training  ${TEST_FAIL_MT_NAME}  AND
...                 Remove File  ${LOCAL_CONFIG}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started  ${TEST_MD_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_1}  AND
...                 Run EDI deploy and check model started  ${TEST_MD_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_2}  AND
...                 Run EDI deploy and check model started  ${TEST_FAIL_MD_NAME}   ${TEST_FAIL_MODEL_IMAGE}   ${TEST_MODEL_NAME}  ${TEST_FAIL_MODEL_VERSION}
Test Teardown       Run Keywords
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_1}     AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_2}     AND
...                 Run EDI undeploy model and check    ${TEST_FAIL_MD_NAME}  AND
...                 Shell  legionctl --verbose mr delete ${TEST_MR_NAME} --ignore-not-found
Force Tags          edi  route

*** Keywords ***
Check mr
    [Arguments]  ${url}
    ${res}=  Shell  legionctl --verbose mr get ${TEST_MR_NAME}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stdout}  ${TEST_MR_NAME}
             Should contain   ${res.stdout}  ${url}
             Should contain   ${res.stdout}  stub-model-6-5-1=100

Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose mr create -f ${LEGION_ENTITIES_DIR}/mr/${create_file}
             Should be equal  ${res.rc}  ${0}

    Check mr  ${EDGE_URL}${TEST_MR_URL_PREFIX}/original

    ${res}=  Shell  legionctl --verbose mr edit -f ${LEGION_ENTITIES_DIR}/mr/${edit_file}
             Should be equal  ${res.rc}  ${0}

    Check mr  ${EDGE_URL}${TEST_MR_URL_PREFIX}/changed

    ${res}=  Shell  legionctl --verbose mr delete -f ${LEGION_ENTITIES_DIR}/mr/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mr get ${TEST_MR_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose mr ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose mr ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Provide name of a Model Route or path to a file
Check model counter
    [Arguments]  ${md_name}
        ${res}=  Shell  legionctl --verbose model invoke --md ${md_name} -p a=1 -p b=2
                 Should be equal  ${res.rc}  ${0}
                 ${RESPONSE}=  evaluate  json.loads('''${res.stdout}'''.replace("\\'", "\\""))  json
                 should be true  ${RESPONSE["result"]} > 0

*** Test Cases ***
Getting of nonexistent Route by name
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose mr get ${TEST_MR_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Basic routing
    [Documentation]  Basic route
    StrictShell  legionctl --verbose mr create ${TEST_MR_NAME} --url-prefix ${TEST_MR_URL_PREFIX} -t ${TEST_MD_NAME_1}=50 -t ${TEST_MD_NAME_2}=50
    ${TOKEN}=  Get token from EDI  ${TEST_MD_NAME_1}

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    ${res}=  Shell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} -p a=1 -p b=2 --jwt ${TOKEN}
    \    Should be equal  ${res.rc}  ${0}

    Check model counter  ${TEST_MD_NAME_1}
    Check model counter  ${TEST_MD_NAME_2}

Basic mirroring
    [Documentation]  Route with mirroring
    StrictShell  legionctl --verbose mr create ${TEST_MR_NAME} --url-prefix ${TEST_MR_URL_PREFIX} -t ${TEST_MD_NAME_1} --mirror ${TEST_MD_NAME_2}
    ${TOKEN}=  Get token from EDI  ${TEST_MD_NAME_1}

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    ${res}=  Shell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} -p a=1 -p b=2 --jwt ${TOKEN}
    \    Should be equal  ${res.rc}  ${0}

    Check model counter  ${TEST_MD_NAME_1}
    Check model counter  ${TEST_MD_NAME_2}

Mirror to broken model
    [Documentation]  Mirror traffic to broken model
    StrictShell  legionctl --verbose mr create ${TEST_MR_NAME} --url-prefix ${TEST_MR_URL_PREFIX} -t ${TEST_MD_NAME_1} --mirror ${TEST_FAIL_MD_NAME}
    ${TOKEN}=  Get token from EDI  ${TEST_MD_NAME_1}

    # TODO: For now we can't control virtual service readiness.
    sleep  5s

    : FOR    ${INDEX}    IN RANGE    1    20
    \    ${res}=  Shell  legionctl --verbose model invoke --url-prefix ${TEST_MR_URL_PREFIX} -p a=1 -p b=2 --jwt ${TOKEN}
    \    Should be equal  ${res.rc}  ${0}

    Check model counter  ${TEST_MD_NAME_1}

Check commands with file parameters
    [Documentation]  Model Route commands with differenet file formats
    [Template]  Check commands with file parameter
    create_file=k8s.json     edit_file=k8s-changed.yaml     delete_file=k8s-changed

File with entitiy not found
    [Documentation]  Invoke Model Route commands with not existed file
    [Template]  File not found
    command=create
    command=edit
    command=delete

User must specify filename or Model Route name
    [Documentation]  Invoke Model Route commands without paramteres
    [Template]  Invoke command without parameters
    command=create
    command=edit
    command=delete

Scaledown to zero pods
    [Documentation]  Mirror traffic to broken model
    Wait model deployment replicas  ${TEST_MD_NAME_1}  ${0}

    Check model counter  ${TEST_MD_NAME_1}

    Wait model deployment replicas  ${TEST_MD_NAME_1}  ${1}