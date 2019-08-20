*** Variables ***
${LOCAL_CONFIG}        legion/config_6_2
${VCS_NAME}            test-vcs-6-2
${VCS_CREDENTIAL}      a2VrCg==
${VCS_GIT_URL}         git@github.com:legion-platform/legion.git
${VCS_REFENRECE}       origin/develop
${VCS_NEW_CREDENTIAL}  bG9sCg==
${VCS_NEW_GIT_URL}     git@github.com:legion-platform/legion-aws.git
${VCS_NEW_REFENRECE}   origin/feat

*** Settings ***
Documentation       Legion's EDI operational check for operations on VCSCredentials resources
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps  vcs
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_CONTEXT}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    Shell  legionctl --verbose vcs delete ${VCS_NAME}

Check vcs
    [Arguments]  ${name}  ${type}  ${reference}  ${creds}
    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME} --show-secrets
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stdout}  ${name}
             Should contain   ${res.stdout}  ${type}
             Should contain   ${res.stdout}  ${reference}
             Should contain   ${res.stdout}  ${creds}

Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose vcs create -f ${LEGION_ENTITIES_DIR}/vcs/${create_file}
             Should be equal  ${res.rc}  ${0}

    Check vcs  ${VCS_NAME}  git  ${VCS_REFENRECE}  ${VCS_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose vcs edit -f ${LEGION_ENTITIES_DIR}/vcs/${edit_file}
             Should be equal  ${res.rc}  ${0}

    Check vcs  ${VCS_NAME}  git  ${VCS_REFENRECE}  ${VCS_NEW_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose vcs delete -f ${LEGION_ENTITIES_DIR}/vcs/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose vcs ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose vcs ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Provide name of a VCS Credential or path to a file

*** Test Cases ***
Getting of nonexistent VCS by name
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Getting of all VCS
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose vcs get
             Should be equal  ${res.rc}  ${0}
             Should not contain   ${res.stderr}  ${VCS_NAME}

Creating of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by name
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    Check vcs  ${VCS_NAME}  git  ${VCS_REFENRECE}  ${VCS_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not contain   ${res.stdout}  ${VCS_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME} --show-secrets
             Should contain   ${res.stdout}  ${VCS_CREDENTIAL}

Creating of a VCS with wrong type
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type wrong-type --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  is invalid

Creating of a VCS without required paramters
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  spec.type in body should be one of

Deleting of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by name
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs delete ${VCS_NAME}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Deleting of nonexistent VCS
    [Documentation]  The scale command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose vcs delete ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Editing of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by name
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs edit ${VCS_NAME} --type git --uri ${VCS_NEW_GIT_URL} --default-reference ${VCS_NEW_REFENRECE} --credential ${VCS_NEW_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    Check vcs  ${VCS_NAME}  git  ${VCS_NEW_REFENRECE}  ${VCS_NEW_CREDENTIAL}

Check commands with file parameters
    [Documentation]  Vcs commands with differenet file formats
    [Template]  Check commands with file parameter
    create_file=k8s.json     edit_file=k8s-changed.yaml     delete_file=k8s-changed

File with entitiy not found
    [Documentation]  Invoke vcs commands with not existed file
    [Template]  File not found
    command=create
    command=edit
    command=delete

User must specify filename or vcs name
    [Documentation]  Invoke vcs commands without paramteres
    [Template]  Invoke command without parameters
    command=create
    command=edit
    command=delete