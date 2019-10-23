*** Variables ***
${LOCAL_CONFIG}         legion/config_conn_cli
${RES_DIR}              ${CURDIR}/resources
${CONN_MAIN_ID}         main-test-conn
${NEW_CONN_MAIN_ID}     new-main-test-conn
${CONN_CREDENTIAL}      a2VrCg==
${CONN_GIT_URL}         git@github.com:legion-platform/legion.git
${CONN_REFENRECE}       origin/develop
${CONN_NEW_CREDENTIAL}  bG9sCg==
${CONN_NEW_GIT_URL}     git@github.com:legion-platform/legion-aws.git
${CONN_NEW_REFENRECE}   origin/feat

*** Settings ***
Documentation       Legion's EDI operational check for operations on connection resources
Test Timeout        20 minutes
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Force Tags          connection  cli  edi
Suite Setup         Run keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Run keywords  Cleanup resources  AND
...                               Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID} --ignore-not-found
    Shell  legionctl --verbose conn delete --id ${NEW_CONN_MAIN_ID} --ignore-not-found

Check conn
    [Arguments]  ${id}  ${type}  ${reference}  ${keySecret}
    ${res}=  Shell  legionctl --verbose conn get --id ${id} -o json
    Should be equal  ${res.rc}      ${0}
    ${conn}=    Evaluate     json.loads("""${res.stdout}""")[0]    json
    should be equal  ${conn['id']}                 ${id}
    should be equal  ${conn['spec']['type']}       ${type}
    should be equal  ${conn['spec']['reference']}  ${reference}
    should be equal  ${conn['spec']['keySecret']}  ${keySecret}

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose conn ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose conn ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Missing option

*** Test Cases ***
Getting of nonexistent connection by name
    ${res}=  Shell  legionctl --verbose conn get --id ${CONN_MAIN_ID}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Getting of all connection
    ${res}=  Shell  legionctl --verbose conn get
             Should be equal  ${res.rc}  ${0}
             Should not contain   ${res.stderr}  ${CONN_MAIN_ID}

Creating of a connection
    [Teardown]  Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/git.json
             Should be equal  ${res.rc}  ${0}

    Check conn  ${CONN_MAIN_ID}  git  ${CONN_REFENRECE}  ${CONN_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose conn get --id ${CONN_MAIN_ID}
             Should contain   ${res.stdout}  ${CONN_MAIN_ID}

Override id during creating of a connection
    [Teardown]  Shell  legionctl --verbose conn delete --id ${NEW_CONN_MAIN_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/git.json --id ${NEW_CONN_MAIN_ID}
             Should be equal  ${res.rc}  ${0}

    Check conn  ${NEW_CONN_MAIN_ID}  git  ${CONN_REFENRECE}  ${CONN_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose conn get --id ${NEW_CONN_MAIN_ID}
             Should contain   ${res.stdout}  ${CONN_MAIN_ID}

Creating of a connection with wrong type
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/wrong-type.json
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  Validation of connection is failed

Creating of a connection without required paramters
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/field-missed.json
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  Validation of connection is failed

Deleting of a connection
    [Teardown]  Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/git.json
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose conn get --id ${CONN_MAIN_ID}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Deleting of nonexistent connection
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Editing of a connection
    [Teardown]  Shell  legionctl --verbose conn delete --id ${CONN_MAIN_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/git.json
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose conn edit -f ${RES_DIR}/git-changed
             Should be equal  ${res.rc}  ${0}

    Check conn  ${CONN_MAIN_ID}  git  ${CONN_NEW_REFENRECE}  ${CONN_NEW_CREDENTIAL}

Override id during editing of a connection
    [Teardown]  Shell  legionctl --verbose conn delete --id ${NEW_CONN_MAIN_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose conn create --id ${NEW_CONN_MAIN_ID} -f ${RES_DIR}/git.json
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose conn edit --id ${NEW_CONN_MAIN_ID} -f ${RES_DIR}/git-changed
             Should be equal  ${res.rc}  ${0}

    Check conn  ${NEW_CONN_MAIN_ID}  git  ${CONN_NEW_REFENRECE}  ${CONN_NEW_CREDENTIAL}

Check commands with file parameters
    [Documentation]  Connections commands with differenet file formats
    ${res}=  Shell  legionctl --verbose conn create -f ${RES_DIR}/git.json
             Should be equal  ${res.rc}  ${0}

    Check conn  ${CONN_MAIN_ID}  git  ${CONN_REFENRECE}  ${CONN_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose conn edit -f ${RES_DIR}/git-changed.yaml
             Should be equal  ${res.rc}  ${0}

    Check conn  ${CONN_MAIN_ID}  git  ${CONN_NEW_REFENRECE}  ${CONN_NEW_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose conn delete -f ${RES_DIR}/git-changed
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose conn get --id ${CONN_MAIN_ID}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File with entitiy not found
    [Documentation]  Invoke connections commands with not existed file
    [Template]  File not found
    command=create
    command=edit
    command=delete
