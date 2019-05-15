*** Variables ***
${LOCAL_CONFIG}        legion/config_6_2
${VCS_NAME}            test-vcs
${VCS_CREDENTIAL}      a2VrCg==
${VCS_GIT_URL}         git@github.com:legion-platform/legion.git
${VCS_REFENRECE}       origin/develop
${VCS_NEW_CREDENTIAL}  bG9sCg==
${VCS_NEW_GIT_URL}     git@github.com:legion-platform/legion-aws.git
${VCS_NEW_REFENRECE}   origin/feat

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge
Suite Teardown      Remove File  ${LOCAL_CONFIG}

*** Test Cases ***
Getting of nonexistent VCS by name
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Getting of all VCS
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose vcs get
             Should be equal  ${res.rc}  ${0}
             Should not contain   ${res.stderr}  ${VCS_NAME}

Creating of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by id
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  ${VCS_NAME}
             Should contain   ${res.stdout}  git
             Should contain   ${res.stdout}  ${VCS_REFENRECE}
             Should not contain   ${res.stdout}  ${VCS_CREDENTIAL}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME} --show-secrets
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  ${VCS_NAME}
             Should contain   ${res.stdout}  git
             Should contain   ${res.stdout}  ${VCS_REFENRECE}
             Should contain   ${res.stdout}  ${VCS_CREDENTIAL}

Creating of a VCS with wrong type
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type wrong-type --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  is invalid

Creating of a VCS without required paramters
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  are required

Deleting of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by id
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs delete ${VCS_NAME}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Deleting of nonexistent VCS
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose vcs delete ${VCS_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Editing of a VCS
    [Documentation]  The scale command must fail if a model cannot be found by id
    [Teardown]  Shell  legionctl --verbose vcs delete ${VCS_NAME}
    ${res}=  Shell  legionctl --verbose vcs create ${VCS_NAME} --type git --uri ${VCS_GIT_URL} --default-reference ${VCS_REFENRECE} --credential ${VCS_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs edit ${VCS_NAME} --type git --uri ${VCS_NEW_GIT_URL} --default-reference ${VCS_NEW_REFENRECE} --credential ${VCS_NEW_CREDENTIAL}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose vcs get ${VCS_NAME} --show-secrets
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  ${VCS_NAME}
             Should contain   ${res.stdout}  git
             Should contain   ${res.stdout}  ${VCS_NEW_REFENRECE}
             Should contain   ${res.stdout}  ${VCS_NEW_CREDENTIAL}
