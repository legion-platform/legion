*** Settings ***
Documentation       Check if all core components are secured
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Library             legion.robot.libraries.k8s.K8s  ${LEGION_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Force Tags          core  security  auth
Test Setup          Choose cluster context            ${CLUSTER_CONTEXT}

*** Keywords ***

Url stay the same after log in
    [Arguments]  ${service_url}
    ${resp}=  Wait Until Keyword Succeeds  2m  5 sec  Wait Until Keyword Succeeds  2m  5 sec  Request as authorized user  ${service_url}
    should be equal  ${service_url}  ${resp.url}

Authorization should raise auth error if user is not authorized
    [Arguments]  ${service_url}
    ${resp}=  Wait Until Keyword Succeeds  2m  5 sec  Request as unauthorized user  ${service_url}
    Log              Response for ${service_url} is ${resp}
    Should contain   ${resp.text}    Log in to
    Should contain   ${resp.text}    Username or email
    Should contain   ${resp.text}    Password

*** Test Cases ***
Service url stay the same after log in
    [Tags]  apps
    [Documentation]  Service url stay the same after log in
    [Template]    Url stay the same after log in
    service_url=${DASHBOARD_URL}/?a=1
    service_url=${EDI_URL}/swagger/index.html
    service_url=${GRAFANA_URL}/?orgId=1&x=2
    service_url=${PROMETHEUS_URL}/graph?x=2&y=3
    service_url=${ALERTMANAGER_URL}/?orgId=1&x=2
    service_url=${JUPYTERLAB_URL}/lab


Invalid credentials raise Auth error
    [Tags]  apps  e2t
    [Documentation]  Invalid credentials raise Auth error
    [Template]    Authorization should raise auth error if user is not authorized
    service_url=${EDI_URL}/swagger/index.html
    service_url=${GRAFANA_URL}/?orgId=1&x=2
    service_url=${PROMETHEUS_URL}/graph?x=2&y=3
    service_url=${ALERTMANAGER_URL}/?orgId=1&x=2
    service_url=${JUPYTERLAB_URL}/lab
