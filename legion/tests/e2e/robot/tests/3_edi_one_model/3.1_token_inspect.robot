*** Variables ***
${LOCAL_CONFIG}        legion/config_31_11
${TEST_MODEL_NAME}     stub-model-31-11
${TEST_MODEL_ID}       31
${TEST_MODEL_VERSION}  11

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run Keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                               Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                               Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                               Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
Suite Teardown      Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}
Test Setup          Run EDI deploy and check model started            ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}   ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
Test Teardown       Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
Force Tags          edi  cli  enclave

*** Test Cases ***
Check if EDGE has been secured by token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info without token
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_ID}/${TEST_MODEL_VERSION}/info
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required

Check if EDGE does not authorize with invalid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with invalid token
     ${invalid_token} =   Set Variable    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MzU2NDA5MDd9.-LIIJjF-Gf37eFbFl0Q_PpQyYWW_A-D9xNW7hsr4Efk
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_ID}/${TEST_MODEL_VERSION}/info  ${invalid_token}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required

Check if EDGE authorize with valid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with valid token
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_ID}/${TEST_MODEL_VERSION}/info  ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    200
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should not contain   ${auth_page}    401 Authorization Required

Check if EDGE don't authorize with other model version valid token
     [Tags]  edi_token
     [Documentation]  Deploy one model, and try to get model info with valid token for another model version
     ${TOKEN}=       Get token from EDI    ${TEST_MODEL_ID}    2
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_ID}/2/info  ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required

Check if EDGE don't authorize with other model id valid token
     [Tags]  edi_token
     [Documentation]  Deploy one model, and try to get model info with valid token for another model version
     ${TOKEN}=       Get token from EDI    ${TEST_MODEL_ID}test    ${TEST_MODEL_VERSION}
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_ID}/2/info  ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required

Get token from EDI with valid parameters
    [Documentation]  Try to get token from EDI with valid parameters
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_id=${TEST_MODEL_ID}    model_version=${TEST_MODEL_VERSION}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
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
    &{data} =     Create Dictionary    model_id=${TEST_MODEL_ID}    model_version=${TEST_MODEL_VERSION}    expiration_date=${expiration_date}
    Log           ${data}
    &{resp} =     Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
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
    &{data} =     Create Dictionary    model_id=${TEST_MODEL_ID}    model_version=${TEST_MODEL_VERSION}    expiration_date=${expiration_date_str}
    Log           ${data}
    &{resp} =     Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log           ${resp}
    Should not be empty    ${resp}
    Should be equal    ${resp["code"]}    ${201}
    &{token} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log           ${token}
    Should not be empty       ${token["token"]}

Get token from EDI without version parameter
    [Documentation]  Try to get token from EDI without version parameter
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_id=${TEST_MODEL_ID}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    500
    &{json} =   Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${json}
    ${items} = 	 Get Dictionary Items    ${json}
    Should be equal as strings   ${items}    ['message', 'Requested field model_version is not set']

Get token from EDI without model_id parameter
    [Documentation]  Try to get token from EDI without model_id parameter
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_version=${TEST_MODEL_VERSION}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/v1/model/token    json_data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    500
    &{json} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${json}
    ${items} = 	 Get Dictionary Items    ${json}
    Should be equal as strings   ${items}   ['message', 'Requested field model_id is not set']

Check EDI enclave inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should contain                 ${resp.stdout}      ${TEST_MODEL_NAME}

Check EDI enclave inspect procedure without deployed model
    [Setup]         NONE
    [Documentation]  Try inspect through EDI console on empty enclave
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should Not Contain             ${resp.stdout}      ${TEST_MODEL_NAME}
