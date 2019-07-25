*** Variables ***
${LOCAL_CONFIG}        legion/config_31_11
${TEST_MT_NAME}        stub-model-31-11
${TEST_MD_NAME}        stub-model-31-11
${TEST_ROLE_NAME}      stub-model-31-11
${TEST_MODEL_NAME}     31
${TEST_MODEL_VERSION}  11

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.k8s.K8s  ${LEGION_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run Keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Build model  ${TEST_MT_NAME}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  AND
...                               Get token from EDI  ${TEST_MD_NAME}  ${TEST_MD_NAME}  AND
...                               Run EDI undeploy model and check    ${TEST_MD_NAME}
Suite Teardown      Run Keywords  Delete model training  ${TEST_MT_NAME}  AND
...                               Run EDI undeploy model and check    ${TEST_MD_NAME}
Test Setup          Run EDI deploy and check model started            ${TEST_MD_NAME}   ${TEST_MODEL_IMAGE}   ${TEST_MODEL_NAME}    ${TEST_MODEL_VERSION}  ${TEST_ROLE_NAME}
Test Teardown       Run EDI undeploy model and check    ${TEST_MD_NAME}
Force Tags          edi  cli  enclave

*** Test Cases ***
Working directory
    [Documentation]  Check that python modules and resource files are accessible from working directory
    [Tags]  apps
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} --endpoint workdir -p value=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Check if EDGE has been secured by token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info without token
     &{response}=    Get component auth page    ${EDGE_URL}/model/${TEST_MD_NAME}/api/model/info
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    Jwt is missing

Check if EDGE does not authorize with invalid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with invalid token
     ${invalid_token} =   Set Variable    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MzU2NDA5MDd9.-LIIJjF-Gf37eFbFl0Q_PpQyYWW_A-D9xNW7hsr4Efk
     &{response}=    Get component auth page    ${EDGE_URL}/model/${TEST_MD_NAME}/api/model/info  ${invalid_token}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    Jwt header [alg] field value is invalid

Check if EDGE authorize with valid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with valid token
     &{response}=    Get component auth page    ${EDGE_URL}/model/${TEST_MD_NAME}/api/model/info  ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    200
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should not contain   ${auth_page}    401 Authorization Required

Get token from EDI with valid parameters
    [Documentation]  Try to get token from EDI with valid parameters
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    role_name=${TEST_ROLE_NAME}
    &{resp} =    Execute post request    ${EDI_URL}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal    ${resp["code"]}    ${201}
    &{token} =   Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${token}
    Should not be empty   ${token["token"]}

Get token from EDI with expiration date set
    [Documentation]  Try to get token from EDI with valid parameters and expiration date set
    [Setup]   NONE
    [Tags]  edi_token
    ${date_format}  Set variable  %Y-%m-%dT%H:%M:%S
    ${expiration_date} =  Get future time  ${60}  ${date_format}
    Log           ${expiration_date}
    &{data} =     Create Dictionary    role_name=${TEST_ROLE_NAME}    expiration_date=${expiration_date}
    Log           ${data}
    &{resp} =     Execute post request    ${EDI_URL}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log           ${resp}
    Should not be empty    ${resp}
    Should be equal    ${resp["code"]}    ${201}
    &{token} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log           ${token}
    Should not be empty       ${token["token"]}

Get token from EDI with too long expiration date set
    [Documentation]  Try to get token from EDI with valid parameters and expiration date set
    [Setup]   NONE
    [Tags]  edi_token
    ${date_format}  Set variable  %Y-%m-%dT%H:%M:%S
    ${expiration_date_str} =  Get future time  ${31104000}  ${date_format}  # 360 days
    Log           ${expiration_date_str}
    &{data} =     Create Dictionary    role_name=${TEST_ROLE_NAME}    expiration_date=${expiration_date_str}
    Log           ${data}
    &{resp} =     Execute post request    ${EDI_URL}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log           ${resp}
    Should not be empty    ${resp}
    Should be equal    ${resp["code"]}    ${201}
    &{token} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log           ${token}
    Should not be empty       ${token["token"]}

Get token from EDI without role_name parameter
    [Documentation]  Try to get token from EDI without model_name parameter
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary
    &{resp} =    Execute post request    ${EDI_URL}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    ${201}
    &{token} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log           ${token}
    Should not be empty       ${token["token"]}

Check EDI enclave inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should contain                 ${resp.stdout}      ${TEST_MD_NAME}

Check EDI enclave inspect procedure without deployed model
    [Setup]         NONE
    [Documentation]  Try inspect through EDI console on empty enclave
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should Not Contain             ${resp.stdout}      ${TEST_MD_NAME}

Get token from EDI with expiration date set
    [Documentation]  Try to get token from EDI and set it`s expiration date
    [Tags]  one_version  apps
    ${expiration_date} =    Get future time           ${40}  %Y-%m-%dT%H:%M:%S
    Log  ${expiration_date}
    ${res} =                StrictShell           legionctl --verbose generate-token --expiration-date ${expiration_date} --md ${TEST_MD_NAME} --role ${TEST_ROLE_NAME}
                            Log  ${res.stdout}
    ${token} =              Set variable          ${res.stdout}
    ${res}=                 StrictShell           legionctl --verbose model info --md ${TEST_MD_NAME} --jwt ${token}
                            Should not contain    ${res.stdout}    401 Authorization Required
                            Should contain        ${res.stdout}    ${TEST_MODEL_NAME}

    Wait Until Keyword Succeeds  3 min  5 sec  FailedShell  legionctl --verbose model info --md ${TEST_MD_NAME} --jwt ${token}
