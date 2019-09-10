*** Variables ***
${LOCAL_CONFIG}         legion/config_common_login

*** Settings ***
Documentation       Login cli command
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Resource            ../../resources/keywords.robot
Force Tags          cli  common  security
Suite Setup         Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}
Suite Teardown      Remove file  ${LOCAL_CONFIG}

*** Test Cases ***
Verifying of a valid token
    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
    Should be equal  ${res.rc}  ${0}
    should contain  ${res.stdout}  Success! Credentials have been saved

Verifying of a not valid token
    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "not-valid-token"
    Should not be equal  ${res.rc}  ${0}
    should contain  ${res.stderr}  Credentials are not correct
