*** Variables ***
${LOCAL_CONFIG}         legion/config_6_3
${TRAINING_NAME}        test-mt
${TRAINING_ARGS}        --id test --version 2.0
${TRAINING_NEW_ARGS}    --id new-test --version 3.0
${TRAINING_WORKDIR}     legion/tests/e2e/models
${TRAINING_ENTRYPOINT}  simple.py
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

*** Keywords ***
Check model training
    [Arguments]  ${state}  ${args}
    ${model_build_status}=  Get model training status  ${TRAINING_NAME}
    ${model_image}=  Get From Dictionary  ${model_build_status}  modelImage

    ${res}=  Shell  legionctl --verbose mt get ${TRAINING_NAME}
             Should be equal  ${res.rc}      ${0}
             Should contain   ${res.stdout}  ${TRAINING_NAME}
             Should contain   ${res.stdout}  ${state}
             Should contain   ${res.stdout}  ${args}
             Should contain   ${res.stdout}  ${TRAINING_TOOLCHAIN}
             Should contain   ${res.stdout}  ${TRAINING_VCS}
             Should contain   ${res.stdout}  ${model_image}

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
                 Should contain       ${res.stderr}  No such file or directory

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
    [Documentation]  The delete command must fail if a training cannot be found by id
    ${res}=  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
             Should not be equal  ${res.rc}  ${0}
             Should contain   ${res.stderr}  not found

Failed Training
    [Documentation]  Check logs and pod state after failed training
    [Teardown]  Shell  legionctl --verbose mt delete ${TRAINING_NAME}
    ${res}=  Shell  legionctl --verbose mt create ${TRAINING_NAME} --timeout ${TRAINING_TIMEOUT} --workdir ${TRAINING_WORKDIR} --toolchain ${TRAINING_TOOLCHAIN} --vcs ${TRAINING_VCS} -e '${TRAINING_ENTRYPOINT}' -a 'echo training is failed ; exit 1'
             Should not be equal  ${res.rc}  ${0}

    ${logs}=  Get model training logs  ${TRAINING_NAME}
    Should contain  ${logs}  training is failed

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
    create_file=legion.json  edit_file=legion-changed.yaml  delete_file=legion-changed

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
