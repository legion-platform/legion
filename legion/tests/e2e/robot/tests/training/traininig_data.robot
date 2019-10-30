*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}         legion/config_training_training_data
# This value locates in the legion/tests/stuf/data/legion.project.yaml file.
${RUN_ID}    training_data_test
${TRAIN_ID}  test-downloading-training-data

*** Settings ***
Documentation       Check downloading of a training data
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Resource            ../../resources/keywords.robot
Library             Collections
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources
Suite Teardown      Run Keywords
...                 Cleanup resources  AND
...                 Remove file  ${LOCAL_CONFIG}
Force Tags          training  training-data

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose train delete --id ${TRAIN_ID} --ignore-not-found

Train valid model
    [Arguments]  ${training_file}
    Cleanup resources

    StrictShell  legionctl --verbose train create -f ${RES_DIR}/valid/${training_file} --id ${TRAIN_ID}
    ${res}=  StrictShell  legionctl train get --id ${TRAIN_ID} -o 'jsonpath=$[0].status.artifacts[0].runId'
    should be equal  ${RUN_ID}  ${res.stdout}

Train invalid model
    [Arguments]  ${training_file}
    Cleanup resources

    ${res}=  Shell  legionctl --verbose train create -f ${RES_DIR}/invalid/${training_file} --id ${TRAIN_ID}
    should not be equal  ${0}  ${res.rc}

*** Test Cases ***
Vaild data downloading parameters
    [Documentation]  Verify various valid combination of connection uri, remote path and local path parameters
    [Template]  Train valid model
    dir_to_dir.training.legion.yaml
    remote_dir_to_dir.training.legion.yaml
    file_to_file.training.legion.yaml
    remote_file_to_file.training.legion.yaml

Invaild data downloading parameters
    [Documentation]  Verify various invalid combination of connection uri, remote path and local path parameters
    [Template]  Train invalid model
    not_found_file.training.legion.yaml
    not_found_remote_file.training.legion.yaml
    not_valid_dir_path.training.legion.yaml
    not_valid_remote_dir.training.legion.yaml

