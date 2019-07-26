*** Variables ***
${LOCAL_CONFIG}         legion/config_common_config
${TEST_VALUE}           test

*** Settings ***
Documentation       Login cli config command
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Resource            ../../resources/keywords.robot
Force Tags          cli  config  common
Suite Setup         Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}
Suite Teardown      Remove file  ${LOCAL_CONFIG}

*** Test Cases ***
All parameters
    ${res}=  Shell  legionctl --verbose config all
    Should be equal  ${res.rc}  ${0}
    should contain  ${res.stdout}  EDI_URL
    should contain  ${res.stdout}  EDI_TOKEN

Config path
    ${res}=  Shell  legionctl --verbose config path
    Should be equal  ${res.rc}  ${0}
    should contain  ${res.stdout}  ${LOCAL_CONFIG}

Set config value
    ${res}=  Shell  legionctl --verbose config get SANDBOX_DOCKER_MOUNT_PATH
    Should be equal  ${res.rc}  ${0}
    should not contain  ${res.stdout}  ${TEST_VALUE}

    ${res}=  Shell  legionctl --verbose config set SANDBOX_DOCKER_MOUNT_PATH test
    Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose config get SANDBOX_DOCKER_MOUNT_PATH
    Should be equal  ${res.rc}  ${0}
    should contain  ${res.stdout}  ${TEST_VALUE}
