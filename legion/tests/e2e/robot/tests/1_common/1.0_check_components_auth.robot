*** Settings ***
Documentation       Check if all core components are secured
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion.robot.libraries.k8s.K8s
Library             legion.robot.libraries.utils.Utils
Force Tags          core  security  auth
Test Setup          Choose cluster context            ${CLUSTER_NAME}

*** Test Cases ***
Check if K8S dashboard domain has been secured
    [Tags]  infra
    [Template]    Check if component domain has been secured
    component=dashboard    enclave=${EMPTY}

Check if Jenkins domain has been secured
    [Tags]  apps
    [Template]    Check if component domain has been secured
    component=jenkins    enclave=${EMPTY}

Check if Grafana domain has been secured
    [Template]    Check if component domain has been secured
    component=grafana    enclave=${EMPTY}

Check if Grafana enclave domain has been secured
    [Tags]  apps
    [Template]    Check if component domain has been secured
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if K8S dashboard domain does not auth with invalid creds
    [Tags]  infra
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=dashboard    enclave=${EMPTY}

Check if Jenkins domain does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=jenkins    enclave=${EMPTY}

Check if Grafana domain does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=grafana    enclave=${EMPTY}

Check if Grafana enclave does not auth with invalid creds
    [Tags]  apps
    [Template]    Secured component domain should not be accessible by invalid credentials
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if Jenkins domain can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=jenkins    enclave=${EMPTY}

Check if Grafana enclave can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=grafana    enclave=${MODEL_TEST_ENCLAVE}

Check if K8S dashboard domain can auth with valid creds
    [Tags]  infra
    [Template]    Secured component domain should be accessible by valid credentials
    component=Dashboard    enclave=${EMPTY}

Check if Grafana domain can auth with valid creds
    [Tags]  apps
    [Template]    Secured component domain should be accessible by valid credentials
    component=grafana    enclave=${EMPTY}

Check if EDGE has been secured by token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info without token
     ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_6}
                     Should Be Equal As Integers         ${resp.rc}         0
     ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_6_VERSION}
                     Should contain                      ${resp}                 "model_version": "${TEST_MODEL_6_VERSION}"
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_6_ID}/${TEST_MODEL_6_VERSION}/info
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required
     [Teardown]      Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}   ${TEST_MODEL_6_VERSION}   ${TEST_MODEL_IMAGE_6}

Check if EDGE does not authorize with invalid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with invalid token
     ${invalid_token} =   Set Variable    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MzU2NDA5MDd9.-LIIJjF-Gf37eFbFl0Q_PpQyYWW_A-D9xNW7hsr4Efk
     ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_6}
                     Should Be Equal As Integers         ${resp.rc}         0
     ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_6_VERSION}
                     Should contain                      ${resp}                 "model_version": "${TEST_MODEL_6_VERSION}"
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_6_ID}/${TEST_MODEL_6_VERSION}/info     ${EMPTY}    ${invalid_token}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required
     [Teardown]      Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}   ${TEST_MODEL_6_VERSION}   ${TEST_MODEL_IMAGE_6}

Check if EDGE authorize with valid token
     [Tags]  apps
     [Documentation]  Deploy one model, and try to get model info with valid token
     ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_6}
                     Should Be Equal As Integers         ${resp.rc}         0
     ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_6_VERSION}
                     Should contain                      ${resp}                 "model_version": "${TEST_MODEL_6_VERSION}"
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_6_ID}/${TEST_MODEL_6_VERSION}/info     ${EMPTY}    ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    200
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should not contain   ${auth_page}    401 Authorization Required
     [Teardown]      Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}   ${TEST_MODEL_6_VERSION}   ${TEST_MODEL_IMAGE_6}

Check if EDGE don't authorize with other model version valid token
     [Tags]  edi_token
     [Documentation]  Deploy one model, and try to get model info with valid token for another model version
     ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_6}
                     Should Be Equal As Integers         ${resp.rc}         0
     ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_6_VERSION}
                     Should contain                      ${resp}                 "model_version": "${TEST_MODEL_6_VERSION}"
     ${TOKEN}=       Get token from EDI    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_2_VERSION}
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_6_ID}/${TEST_MODEL_2_VERSION}/info     ${EMPTY}    ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required
     [Teardown]      Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}   ${TEST_MODEL_6_VERSION}   ${TEST_MODEL_IMAGE_6}

Check if EDGE don't authorize with other model id valid token
     [Tags]  edi_token
     [Documentation]  Deploy one model, and try to get model info with valid token for another model version
     ${resp}=        Run EDI deploy                      ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_6}
                     Should Be Equal As Integers         ${resp.rc}         0
     ${resp}=        Check model started                 ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}    ${TEST_MODEL_6_VERSION}
                     Should contain                      ${resp}                 "model_version": "${TEST_MODEL_6_VERSION}"
     ${TOKEN}=       Get token from EDI    ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}test    ${TEST_MODEL_6_VERSION}
     &{response}=    Get component auth page    ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_MODEL_6_ID}/${TEST_MODEL_2_VERSION}/info     ${EMPTY}    ${TOKEN}
     Dictionary Should Contain Item    ${response}    response_code    401
     ${auth_page} =  Get From Dictionary   ${response}    response_text
     Should contain   ${auth_page}    401 Authorization Required
     [Teardown]      Run EDI undeploy by model version and check     ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_6_ID}   ${TEST_MODEL_6_VERSION}   ${TEST_MODEL_IMAGE_6}

Service url stay the same after log in
    [Tags]  apps
    [Documentation]  Service url stay the same after log in
    [Template]    Url stay the same after dex log in
    service_url=https://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/healthcheck?xx=22&yy=33
    service_url=https://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/1.0/info?xx=22&yy=33
    service_url=https://grafana-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/?orgId=1&x=2
    service_url=https://grafana.${HOST_BASE_DOMAIN}/?orgId=1&x=2
