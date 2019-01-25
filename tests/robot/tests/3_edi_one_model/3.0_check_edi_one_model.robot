*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Choose cluster context                              ${CLUSTER_NAME}
Test Setup          Run EDI deploy and check model started              ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
Test Teardown       Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
Force Tags          edi  cli  enclave

*** Test Cases ***
Check EDI availability in all enclaves
    [Setup]         NONE
    [Documentation]  Try to connect to EDI in each enclave
    [Tags]  apps
    :FOR    ${enclave}      IN                            @{ENCLAVES}
    \       ${edi_state}=   Run EDI inspect               ${enclave}
    \                       Should Be Equal As Integers   ${edi_state.rc}     0
    [Teardown]              NONE

Get token from EDI with valid parameters
    [Documentation]  Try to get token from EDI with valid parameters
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_id=${TEST_EDI_MODEL_ID}    model_version=${TEST_MODEL_3_VERSION}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/generate_token    data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    200
    &{token} =   Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${token}
    Should not be empty   ${token["token"]}
    Should not be empty   ${token["exp"]}

Get token from EDI and set expiration date
    [Documentation]  Try to get token from EDI with valid parameters and expiration date set
    [Setup]   NONE
    [Tags]  edi_token  unique
    ${date_format}  Set variable  %Y-%m-%dT%H:%M:%S
    ${expiration_date} =  Get future time  60  ${date_format}
    Log           ${expiration_date}
    &{data} =     Create Dictionary    model_id=${TEST_EDI_MODEL_ID}    model_version=${TEST_MODEL_3_VERSION}    expiration_date=${expiration_date}
    Log           ${data}
    &{resp} =     Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/generate_token    data=${data}  cookies=${DEX_COOKIES}
    Log           ${resp}
    Should not be empty    ${resp}
    Should be equal as integers    ${resp["code"]}    200
    &{token} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log           ${token}
    Should not be empty       ${token["token"]}
    Should not be empty       ${token["exp"]}
    ${res_expiration_date} =  Reformat time    ${token["exp"]}    %a, %d %b %Y %H:%M:%S GMT    ${date_format}
    Should be equal           ${res_expiration_date}    ${expiration_date}

Get token from EDI without version parameter
    [Documentation]  Try to get token from EDI without version parameter
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_id=${TEST_EDI_MODEL_ID}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/generate_token    data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    500
    &{json} =   Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${json}
    ${items} = 	 Get Dictionary Items    ${json}
    Should be equal as strings   ${items}    ['error', True, 'exception', 'Requested field model_version is not set']

Get token from EDI without model_id parameter
    [Documentation]  Try to get token from EDI without model_id parameter
    [Setup]   NONE
    [Tags]  edi_token
    &{data} =    Create Dictionary    model_version=${TEST_MODEL_3_VERSION}
    &{resp} =    Execute post request    ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/generate_token    data=${data}  cookies=${DEX_COOKIES}
    Log          ${resp}
    Should not be empty   ${resp}
    Should be equal as integers    ${resp["code"]}    500
    &{json} =    Evaluate    json.loads('''${resp["text"]}''')    json
    Log          ${json}
    ${items} = 	 Get Dictionary Items    ${json}
    Should be equal as strings   ${items}   ['error', True, 'exception', 'Requested field model_id is not set']

Check EDI deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${response}=    Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
                    Should contain                      ${response}             "model_version": "${TEST_MODEL_3_VERSION}"

Check EDI deploy with scale to 0
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}   0
                    Should Be Equal As Integers    ${resp.rc}         2
                    Should contain                 ${resp.stderr}     Invalid scale parameter: should be greater then 0

Check EDI deploy with scale to 1
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}   1
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
                    Should contain                 ${response}             "model_version": "${TEST_MODEL_3_VERSION}"

    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_EDI_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_IMAGE_3}   ${TEST_MODEL_3_VERSION}   1

Check EDI deploy with scale to 2
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy with scale      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}   2
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
                    Should contain                 ${response}             "model_version": "${TEST_MODEL_3_VERSION}"

    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_EDI_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_IMAGE_3}   ${TEST_MODEL_3_VERSION}   2

Check EDI invalid model name deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy dummy invalid model name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}test
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Can't get image labels for  ${TEST_MODEL_IMAGE_3}test

Check EDI double deploy procedure for the same model
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
    [Documentation]  Try to deploy twice the same dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}
                    Should Be Equal As Integers   ${resp.rc}         0
    ${response}=    Check model started           ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
                    Should contain                ${response}             "model_version": "${TEST_MODEL_3_VERSION}"
    ${resp}=        Run EDI deploy                ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_3}
                    Should Be Equal As Integers   ${resp.rc}         0
    ${response}=    Check model started           ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_3_VERSION}
                    Should contain                ${response}             "model_version": "${TEST_MODEL_3_VERSION}"

Check EDI undeploy procedure
    [Documentation]  Try to undeploy dummy valid model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI undeploy without version    ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Run EDI inspect                     ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers         ${resp.rc}         0
                    Should not contain                  ${resp.stdout}     ${TEST_EDI_MODEL_ID}

Check EDI scale up procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_EDI_MODEL_ID}    2
                    Should Be Equal As Integers    ${resp.rc}           0
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_EDI_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_IMAGE_3}   ${TEST_MODEL_3_VERSION}   2

Check EDI scale down procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_EDI_MODEL_ID}    2
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_EDI_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_IMAGE_3}   ${TEST_MODEL_3_VERSION}   2

    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_EDI_MODEL_ID}    1
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse     ${MODEL_TEST_ENCLAVE}
    ${model}=       Find model information in edi  ${resp}    ${TEST_EDI_MODEL_ID}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_EDI_MODEL_ID}    ${TEST_MODEL_IMAGE_3}   ${TEST_MODEL_3_VERSION}   1

Check EDI scale to 0 procedure
    [Documentation]  Try to scale to 0 model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_EDI_MODEL_ID}    0
                    Should Be Equal As Integers    ${resp.rc}          2
                    Should contain                 ${resp.stderr}      Invalid scale parameter: should be greater then 0

Check EDI invalid model id scale up procedure
    [Documentation]  Try to scale up dummy model with invalid name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI scale                ${MODEL_TEST_ENCLAVE}   ${TEST_EDI_MODEL_ID}test   2
                    Should Be Equal As Integers  ${resp.rc}         2
                    Should contain               ${resp.stderr}     No one model can be found

Check EDI enclave inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should contain                 ${resp.stdout}      ${TEST_EDI_MODEL_ID}

Check EDI invalid enclave name inspect procedure
    [Documentation]  Try to inspect enclave through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}test
                    Should Be Equal As Integers    ${resp.rc}          2
                    Should contain                 ${resp.stderr}      ERROR - Failed to connect

Check EDI enclave inspect procedure without deployed model
    [Setup]         NONE
    [Documentation]  Try inspect through EDI console on empty enclave
    [Tags]  one_version  apps
    ${resp}=        Run EDI inspect                ${MODEL_TEST_ENCLAVE}
                    Should Be Equal As Integers    ${resp.rc}          0
                    Should Not Contain             ${resp.stdout}      ${TEST_EDI_MODEL_ID}
