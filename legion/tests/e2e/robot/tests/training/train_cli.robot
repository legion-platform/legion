*** Variables ***
${LOCAL_CONFIG}         legion/config_6_3
${TRAINING_NAME}        test-mt-6-3
${TRAINING_ARGS}        --name test --version 2.0
${TRAINING_NEW_ARGS}    --name new-test --version 3.0
${TRAINING_WORKDIR}     legion/tests/e2e/models
${TRAINING_ENTRYPOINT}  simple.py
${TRAINING_VCS}         legion
${TRAINING_TOOLCHAIN}   python
${TRAINING_TIMEOUT}     200

*** Settings ***
Documentation       Legion's EDI operational check for operations on ModelTraining resources
Test Timeout        20 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_CONTEXT}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Remove File  ${LOCAL_CONFIG}
Force Tags          training  edi  cli  disable

*** Keywords ***
Cleanup resources
    Shell  legionctl --verbose mt delete ${TRAINING_NAME}

Check model training
    [Arguments]  ${state}  ${args}
    ${mt}=  Get model training  ${TRAINING_NAME}

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stdout}  ${TRAINING_NAME}
             Should contain   ${res.stdout}  ${state}
             Should contain   ${res.stdout}  ${args}
             Should contain   ${res.stdout}  ${TRAINING_TOOLCHAIN}
             Should contain   ${res.stdout}  ${TRAINING_VCS}
             Should contain   ${res.stdout}  ${mt.trained_image}

Check commands with file parameter
    [Arguments]  ${create_file}  ${edit_file}  ${delete_file}
    ${res}=  Shell  legionctl --verbose mt create -f ${LEGION_ENTITIES_DIR}/mt/${create_file}
             Should be equal  ${res.rc}  ${0}

    Check model training  succeeded  ${TRAINING_ARGS}

    ${res}=  Shell  legionctl --verbose mt edit -f ${LEGION_ENTITIES_DIR}/mt/${edit_file}
             Should be equal  ${res.rc}  ${0}

    Check model training  succeeded  ${TRAINING_NEW_ARGS}

    ${res}=  Shell  legionctl --verbose mt delete -f ${LEGION_ENTITIES_DIR}/mt/${delete_file}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose mt ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

Invoke command without parameters
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose mt ${command}
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Provide name of a Model Training or path to a file

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
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}

    Check model training  succeeded  ${TRAINING_ARGS}

Deleting of a Model Training
    [Documentation]  Deleting of a Model Training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Deleting of nonexistent Model Training
    [Documentation]  The delete command must fail if a training cannot be found by name
    ${res}=  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Failed Training
    [Documentation]  Check logs and pod state after failed training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}

    ${logs}=  StrictShell  legionctl --verbose mt logs ${TRAINING_NAME}
    Should contain  ${logs.stdout}  training is failed

    Wait Until Keyword Succeeds  2m  5 sec  Check all containers terminated  ${TRAINING_NAME}

Not existed VCS Credential
    [Documentation]  Creation of training must failed if there is vcs credential
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs wrong-vcs -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  not found

Check commands with file parameters
    [Documentation]  Model Trainings commands with differenet file formats
    [Template]  Check commands with file parameter
    create_file=k8s.json     edit_file=k8s-changed.yaml     delete_file=k8s-changed

File with entitiy not found
    [Documentation]  Invoke Model Training commands with not existed file
    [Template]  File not found
    command=create
    command=edit
    command=delete

User must specify filename or mt name
    [Documentation]  Invoke Model Training commands without paramteres
    [Template]  Invoke command without parameters
    command=create
    command=edit
    command=delete

Retraining of failed model and checking of training logs
    [Documentation]  Retrain failed model
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stdout}   training is failed

    ${res}=  Shell  legionctl --verbose mt logs ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}
             should contain  ${res.stdout}   training is failed

    ${res}=  Shell  legionctl --verbose mt edit ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}
             should not contain  ${res.stdout}   training is failed

    ${res}=  Shell  legionctl --verbose mt logs ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}
             should not contain  ${res.stdout}   training is failed

Force model retraining
    [Documentation]  Force retrain failed model
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --no-wait --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose mt edit ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a '${TRAINING_ARGS}'
             Should be equal  ${res.rc}  ${0}
             should not contain  ${res.stdout}   training is failed

    ${res}=  Shell  legionctl --verbose mt logs ${TRAINING_NAME}
             Should be equal  ${res.rc}  ${0}
             should not contain  ${res.stdout}   training is failed
