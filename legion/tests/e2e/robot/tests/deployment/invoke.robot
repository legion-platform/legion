*** Variables ***
${RES_DIR}             ${CURDIR}/resources
${LOCAL_CONFIG}        legion/config_deployment_invoke
${MD_SIMPLE_MODEL}     simple-model-invoke

*** Settings ***
Documentation       Legion's EDI operational check for operations on ModelDeployment resources
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Force Tags          deployment  edi  cli  invoke
Suite Setup         Run Keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Get token from EDI  ${MD_SIMPLE_MODEL}  ${EMPTY}  AND
...                               Cleanup resources  AND
...                               Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/simple-model.deployment.legion.yaml  AND
...                               Check model started  ${MD_SIMPLE_MODEL}
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose dep delete --id ${MD_SIMPLE_MODEL} --ignore-not-found

Refresh security tokens
    [Documentation]  Refresh edi and model tokens. Return model jwt token

    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl dep generate-token --md-id ${MD_SIMPLE_MODEL}
             Should be equal  ${res.rc}  ${0}
    ${JWT}=  Set variable  ${res.stdout}
    ${res}=  Shell  legionctl config set MODEL_HOST ${EDGE_URL}
             Should be equal  ${res.rc}  ${0}

    [Return]  ${JWT}

*** Test Cases ***
Invoke. Empty jwt
    [Documentation]  Fails if jwt is empty
    [Teardown]  Login to the edi and edge
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json-file ${RES_DIR}/simple-model.request.json --host ${EDGE_URL}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Jwt is missing
             Should contain       ${res.stderr}  401

Invoke. Empty model service url
    [Documentation]  Fails if model service url is empty
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --host ${EDGE_URL} --url-prefix /model/${MD_SIMPLE_MODEL} --json-file ${RES_DIR}/simple-model.request.json --jwt "some_token"
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  Jwt is not in the form of Header.Payload.Signature
             Should contain       ${res.stderr}  401

Invoke. Wrong jwt
    [Documentation]  Fails if jwt is wrong
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json-file ${RES_DIR}/simple-model.request.json --host ${EDGE_URL} --jwt wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Jwt is not in the form of Header.Payload.Signature

Invoke. Pass parameters explicitly
    [Documentation]  Pass parameters explicitly
    ${JWT}=  Refresh security tokens
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json-file ${RES_DIR}/simple-model.request.json --host ${EDGE_URL} --jwt "${JWT}"
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass parameters through config file
    [Documentation]  Pass parameters through config file
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json-file ${RES_DIR}/simple-model.request.json
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass model parameters using json
    [Documentation]  Model parameters as json
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json '{"columns": ["a","b"],"data": [[1.0,2.0]]}'
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42
