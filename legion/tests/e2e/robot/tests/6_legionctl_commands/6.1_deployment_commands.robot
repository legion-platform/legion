*** Variables ***
${LOCAL_CONFIG}        legion/config_6_1
${TEST_MT_NAME}        stub-model-6-1
${TEST_MD_NAME}        stub-model-6-1
${TEST_MODEL_NAME}     6
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Legion's EDI operational check for operations on ModelDeployment resources
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps  md
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_CONTEXT}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build model  ${TEST_MT_NAME}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  AND
...                 Get token from EDI  ${TEST_MD_NAME}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME}  AND
...                 Run EDI deploy and check model started  ${TEST_MD_NAME}  ${TEST_MODEL_IMAGE}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}
Suite Teardown      Run keywords  Delete model training  ${TEST_MT_NAME}  AND
...                 Shell  legionctl --verbose md delete ${TEST_MD_NAME}  AND
...                 Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Refresh security tokens
    [Documentation]  Refresh edi and model tokens. Return model jwt token

    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --md ${TEST_MD_NAME} --role ${TEST_MD_NAME}
             Should be equal  ${res.rc}  ${0}
    ${JWT}=  Set variable  ${res.stdout}
    ${res}=  Shell  legionctl config set MODEL_HOST ${EDGE_URL}
             Should be equal  ${res.rc}  ${0}

    [Return]  ${JWT}

*** Test Cases ***
Undeploy. Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose md delete this-model-does-not-exsit
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Undeploy. Nonexistent model service with ignore-not-found parameter
    [Documentation]  The undeploy command must finish successfully if a model does not exists but we there is --ignore-not-found parameter
    ${res}=  Shell  legionctl --verbose md delete this-model-does-not-exsit --ignore-not-found
             Should be equal  ${res.rc}  ${0}

Deploy. Negative liveness timeout
    [Documentation]  The deploy command must fail if liveness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete ${TEST_MD_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --livenesstimeout -3
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  liveness probe parameter must be positive number

Deploy. Negative readiness timeout
    [Documentation]  The deploy command must fail if readiness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete ${TEST_MD_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --readinesstimeout -3
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  readiness probe must be positive number

Deploy. Negative number of max replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete ${TEST_MD_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --max-replicas -3
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  maximum number of replicas parameter must not be less than 1

Deploy. Negative number of min replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete ${TEST_MD_NAME}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --min-replicas -3
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  minimum number of replicas parameter must not be less than 0

Deploy. Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    [Setup]  Shell  legionctl --verbose md delete ${TEST_MD_NAME} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --timeout=0
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    [Setup]  Shell  legionctl --verbose md delete ${TEST_MD_NAME} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --timeout=-500
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Shell  legionctl --verbose md delete ${TEST_MD_NAME} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --no-wait --timeout=-500
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --token "${AUTH_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  EDI endpoint is not configured

Wrong token
    [Documentation]  The inspect command must fail if it does not contain a token
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --edi ${EDI_URL} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Without token
    [Documentation]  The inspect command must fail if token is wrong
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --edi ${EDI_URL}

             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are missed

Login. Basic usage
    [Documentation]  Check the login command and inspect command
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get
             Should be equal  ${res.rc}  ${0}

Login. Wrong token
    [Documentation]  The login command must fail if token is wrong
    ${res}=  Shell  legionctl --verbose md get --edi ${EDI_URL} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Override login values
    [Documentation]  Command line parameters must be overrided by config parameters
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get --edi ${EDI_URL} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Get token from EDI
    [Documentation]  Try to get token from EDI
    ${res} =  Shell  legionctl --verbose generate-token --md ${TEST_MD_NAME}
              Should be equal       ${res.rc}  ${0}
              Should not be empty   ${res.stdout}

    ${res} =  Shell  legionctl --verbose generate-token --md ${TEST_MD_NAME} --token wrong-token
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Credentials are not correct

Deploy fails when memory resource is incorect
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    [Documentation]  Deploy fails when memory resource is incorect
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --memory-limit wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  quantities must match the regular expression

Deploy fails when cpu resource is incorect
    [Setup]         Run EDI undeploy model and check    ${TEST_MD_NAME}
    [Documentation]  Deploy fails when cpu resource is incorect
    ${res}=  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --cpu-request wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  quantities must match the regular expression

Invoke. Empty jwt
    [Documentation]  Fails if jwt is empty
    [Setup]  Shell  legionctl --verbose md create ${TEST_MD_NAME} --image ${TEST_MODEL_IMAGE} --role ${TEST_MD_NAME}
    [Teardown]  Login to the edi and edge
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} -p a=1 -p b=2 --host ${EDGE_URL}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Jwt is missing
             Should contain       ${res.stderr}  401

Invoke. Empty model service url
    [Documentation]  Fails if model service url is empty
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --host ${EDGE_URL} --url-prefix /model/${TEST_MD_NAME} -p a=1 -p b=2 --jwt "some_token"
             Should not be equal  ${res.rc}      ${0}
             Should contain       ${res.stderr}  Jwt is not in the form of Header.Payload.Signature
             Should contain       ${res.stderr}  401

Invoke. Wrong jwt
    [Documentation]  Fails if jwt is wrong
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} -p a=1 -p b=2 --host ${EDGE_URL} --jwt wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Jwt is not in the form of Header.Payload.Signature

Invoke. Pass parameters explicitly
    [Documentation]  Pass parameters explicitly
    ${JWT}=  Refresh security tokens
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}
    StrictShell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"

    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} -p a=1 -p b=2 --host ${EDGE_URL} --jwt "${JWT}"
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass parameters through config file
    [Documentation]  Pass parameters through config file
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} -p a=1 -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Fails with wrong model parameters
    [Documentation]  Fails if model parameters is wrong
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} -p a=1
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Internal Server Error

Invoke. Pass model parameters using json
    [Documentation]  Model parameters as json
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} --json '{"a": 1, "b": 2}'
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass model parameters using json and p
    [Documentation]  Combination json and p model parameters
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} --json '{"a": 1}' -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Specify model endpoint
    [Documentation]  Different model endpoint
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME} --endpoint=feedback -p str=aa -p copies=3
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  aaaaaa
