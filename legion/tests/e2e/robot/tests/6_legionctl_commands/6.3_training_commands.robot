*** Variables ***
${LOCAL_CONFIG}         legion/config_6_3
${TRAINING_NAME}        test-vcs
${TRAINING_ARGS}        --id test --version 2.0
${TRAINING_ENTRYPOINT}  legion/tests/e2e/models/simple.py
${TRAINING_VCS}         legion
${TRAINING_TOOLCHAIN}   python
${TRAINING_TIMEOUT}     200

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
Getting of nonexistent Model Training by name
    [Documentation]  Getting of nonexistent VCS by name is failed
    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Getting of all Model Training
    [Documentation]  Getting of nonexistent Model Training by name
    ${res}=  Shell  legionctl --verbose mt get
             Should be equal  ${res.rc}  ${0}
             Should not contain   ${res.stderr}  ${TRAINING_NAME}

Creating of a Model Training
    [Documentation]  Creating of a Model Training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  ${TRAINING_NAME}
             Should contain   ${res.stdout}  succeeded
             Should contain   ${res.stdout}  ${TRAINING_TOOLCHAIN}
             Should contain   ${res.stdout}  ${TRAINING_VCS}

Deleting of a Model Training
    [Documentation]  Deleting of a Model Training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Deleting of nonexistent Model Training
    [Documentation]  The delete command must fail if a training cannot be found by id
    ${res}=  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Failed Training
    [Documentation]  Check logs and pod state after failed training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}

    ${logs}=  Get model training logs  ${TRAINING_NAME}
    Should contain  ${logs}  training is failed

    Check all containers terminated  ${TRAINING_NAME}

Not existed VCS Credential
    [Documentation]  Creation of training must failed if there is vcs credential
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --toolchain ${TRAINING_TOOLCHAIN} --vcs wrong-vcs -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  not found
