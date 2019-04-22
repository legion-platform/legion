*** Variables ***
${LOCAL_CONFIG}        legion/config_3_0
${TEST_MODEL_NAME}     stub-model-3-1
${TEST_MODEL_ID}       3
${TEST_MODEL_VERSION}  1

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

Check EDI deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Run EDI deploy                      ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${response}=    Check model started                 ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                      ${response}         'model_version': '${TEST_MODEL_VERSION}'

# TODO: revert test after developing of model deployment webhook validation
#Check EDI deploy with scale to 0
#    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
#    [Documentation]  Try to deploy dummy model through EDI console
#    [Tags]  one_version  apps
#    ${resp}=        Run EDI deploy with scale      ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}   -1
#                    Should Be Equal As Integers    ${resp.rc}         2
#                    Should contain                 ${resp.stderr}     Invalid scale parameter: should be greater then 0

Check EDI deploy with scale to 1
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --replicas 1
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                 ${response}         'model_version': '${TEST_MODEL_VERSION}'

    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated  1

Check EDI deploy with scale to 2
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}         0
    ${response}=    Check model started            ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                 ${response}             'model_version': '${TEST_MODEL_VERSION}'

    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2

Check EDI invalid model name deploy procedure
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy dummy invalid model name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell                legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}test
                    Should Be Equal As Integers   ${resp.rc}         2
                    Should Contain                ${resp.stderr}     Label extraction from ${TEST_MODEL_IMAGE}test image is failed

Check EDI double deploy procedure for the same model
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Try to deploy twice the same dummy model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
                    Should Be Equal As Integers   ${resp.rc}         0
    ${response}=    Check model started           ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                ${response}             'model_version': '${TEST_MODEL_VERSION}'
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
                    should not be equal as integers  ${resp.rc}         0
    ${response}=    Check model started           ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
                    Should contain                ${response}             'model_version': '${TEST_MODEL_VERSION}'

Check EDI undeploy procedure
    [Documentation]  Try to undeploy dummy valid model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers         ${resp.rc}         0
    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers         ${resp.rc}         0
                    Should not contain                  ${resp.stdout}     ${TEST_MODEL_NAME}

Check EDI scale up procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}           0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2

Check EDI scale down procedure
    [Documentation]  Try to scale up model through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 2
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   2

    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 1
                    Should Be Equal As Integers    ${resp.rc}          0
    ${resp}=        Run EDI inspect with parse
    ${model}=       Find model information in edi  ${resp}    ${TEST_MODEL_NAME}
                    Log                            ${model}
                    Verify model info from edi     ${model}   ${TEST_MODEL_NAME}  DeploymentCreated   1

# TODO: revert test after developing of model deployment webhook validation
#Check EDI scale to 0 procedure
#    [Documentation]  Try to scale to 0 model through EDI console
#    [Tags]  one_version  apps
#    ${resp}=        Run EDI scale                  ${MODEL_TEST_ENCLAVE}    ${TEST_MODEL_ID}    0
#                    Should Be Equal As Integers    ${resp.rc}          2
#                    Should contain                 ${resp.stderr}      Invalid scale parameter: should be greater then 0

Check EDI invalid model id scale up procedure
    [Documentation]  Try to scale up dummy model with invalid name through EDI console
    [Tags]  one_version  apps
    ${resp}=        Shell  legionctl --verbose md scale ${TEST_MODEL_NAME}-wrong --replicas 2
                    Should Be Equal As Integers  ${resp.rc}         2
                    Should contain               ${resp.stderr}     not found

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

Deploy with custom memory and cpu
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Deploy with custom memory and cpu
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --memory-limit 333Mi --cpu-limit 333m --memory-request 222Mi --cpu-request 222m
         Should be equal  ${res.rc}  ${0}
    ${model_deployment}=  Get model deployment  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${MODEL_TEST_ENCLAVE}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  333m  ${model_resources.limits["cpu"]}
    Should be equal  333Mi  ${model_resources.limits["memory"]}
    Should be equal  222m  ${model_resources.requests["cpu"]}
    Should be equal  222Mi  ${model_resources.requests["memory"]}

# TODO: revert test after developing of model deployment webhook validation
#Check setting of default resource values
#    [Documentation]  Deploy setting of default resource values
#    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
#    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
#             Should be equal  ${res.rc}  ${0}
#    ${model_deployment}=  Get model deployment  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${MODEL_TEST_ENCLAVE}
#    LOG  ${model_deployment}
#
#    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
#    Should be equal  256m  ${model_resources.limits["cpu"]}
#    Should be equal  256Mi  ${model_resources.limits["memory"]}
#    Should be equal  128m  ${model_resources.requests["cpu"]}
#    Should be equal  128Mi  ${model_resources.requests["memory"]}
