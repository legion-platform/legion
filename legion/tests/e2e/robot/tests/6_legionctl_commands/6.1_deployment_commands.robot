*** Variables ***
${LOCAL_CONFIG}  legion/config_6_1
${TEST_MODEL_NAME}     stub-model-6-1
${TEST_MODEL_ID}       6
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Legion's EDI operational check for operations on ModelDeployment resources
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps  md
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}  AND
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME}  ${TEST_MODEL_IMAGE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}
Suite Teardown      Run keywords  Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}  AND
...                 Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Refresh security tokens
    [Documentation]  Refresh edi and model tokens. Return model jwt token

    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION}
             Should be equal  ${res.rc}  ${0}
    ${JWT}=  Set variable  ${res.stdout}
    ${res}=  Shell  legionctl config set MODEL_SERVER_URL https://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
             Should be equal  ${res.rc}  ${0}

    [Return]  ${JWT}

*** Test Cases ***
Scale. Nonexistent model service
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose md scale this-model-does-not-exsit --replicas 1
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Scale. Scale to negative number of replicas
    [Documentation]  The scale command must fail if number of replicas is negative
    ${res}=  Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas -3
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Number of replicas parameter must not be less than 0

Scale. Missed the host parameter
    [Documentation]  The scale command must fail if it does not contain an edi host
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md scale ${TEST_MODEL_NAME} --replicas 2 --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  EDI endpoint is not configured

Undeploy. Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose md delete this-model-does-not-exsit
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Undeploy. Nonexistent version of model service
    [Documentation]  The undeploy command must fail if a model cannot be found by version and id
    ${res}=  Shell  legionctl --verbose md delete --model-version this-version-does-not-exsit
             Should be equal  ${res.rc}  ${0}

Undeploy. Nonexistent model service with ignore-not-found parameter
    [Documentation]  The undeploy command must finish successfully if a model does not exists but we there is --ignore-not-found parameter
    ${res}=  Shell  legionctl --verbose md delete this-model-does-not-exsit --ignore-not-found
             Should be equal  ${res.rc}  ${0}

Deploy. Negative liveness timeout
    [Documentation]  The deploy command must fail if liveness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --livenesstimeout -3
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  Liveness probe parameter must be positive number

Deploy. Negative readiness timeout
    [Documentation]  The deploy command must fail if readiness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --readinesstimeout -3
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  Readiness probe must be positive number

Deploy. Negative number of replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Setup]  Run Keyword And Ignore Error  Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID}
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --replicas -3
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Number of replicas parameter must not be less than 0

Deploy. Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    [Setup]  Shell  legionctl --verbose md delete --model-id ${TEST_MODEL_ID} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --timeout=0
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    [Setup]  Shell  legionctl --verbose md delete ${TEST_MODEL_NAME} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --timeout=-500
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Shell  legionctl --verbose md delete ${TEST_MODEL_NAME} --ignore-not-found
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --no-wait --timeout=-500
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  EDI endpoint is not configured

Wrong token
    [Documentation]  The inspect command must fail if it does not contain a token
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Without token
    [Documentation]  The inspect command must fail if token is wrong
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose md get --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}

             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Basic usage
    [Documentation]  Check the login command and inspect command
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get
             Should be equal  ${res.rc}  ${0}

Login. Wrong token
    [Documentation]  The login command must fail if token is wrong
    ${res}=  Shell  legionctl --verbose md get --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Override login values
    [Documentation]  Command line parameters must be overrided by config parameters
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose md get --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Get token from EDI
    [Documentation]  Try to get token from EDI
    ${res} =  Shell  legionctl --verbose generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION}
              Should be equal       ${res.rc}  ${0}
              Should not be empty   ${res.stdout}

    ${res} =  Shell  legionctl --verbose generate-token --model-id ${TEST_MODEL_ID}
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Requested field model_version is not set

    ${res} =  Shell  legionctl --verbose generate-token --model-version ${TEST_MODEL_VERSION}
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Requested field model_id is not set

    ${res} =  Shell  legionctl --verbose generate-token --model-version ${TEST_MODEL_VERSION} --token wrong-token
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Credentials are not correct

Get token from EDI with expiration date set
    [Documentation]  Try to get token from EDI and set it`s expiration date
    ${expiration_date} =    Get future time           ${40}  %Y-%m-%dT%H:%M:%S
    Log  ${expiration_date}
    ${res} =                StrictShell                   legionctl --verbose generate-token --expiration-date ${expiration_date} --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION}
                            Log  ${res.stdout}
    ${token} =              Set variable          ${res.stdout}
    ${res}=                 StrictShell           legionctl --verbose model info --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} --jwt ${token}
                            Should not contain    ${res.stdout}    401 Authorization Required
                            Should contain        ${res.stdout}    ${TEST_MODEL_ID}
                            Should contain        ${res.stdout}    ${TEST_MODEL_VERSION}

    Wait Until Keyword Succeeds  3 min  5 sec  FailedShell  legionctl --verbose model info --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} --jwt ${token}

Deploy fails when memory resource is incorect
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Deploy fails when memory resource is incorect
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --memory-limit wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  quantities must match the regular expression

Deploy fails when cpu resource is incorect
    [Setup]         Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
    [Documentation]  Deploy fails when cpu resource is incorect
    ${res}=  Shell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE} --cpu-request wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  quantities must match the regular expression

Invoke. Empty model service url
    [Documentation]  Fails if model service url is empty
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1 -p b=2 --jwt "some_token"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  specify model server url

Invoke. Empty jwt
    [Documentation]  Fails if jwt is empty
    [Teardown]  Login to the edi and edge
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}

    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  specify model jwt

Invoke. Wrong jwt
    [Documentation]  Fails if jwt is wrong
    [Setup]  StrictShell  legionctl --verbose md create ${TEST_MODEL_NAME} --image ${TEST_MODEL_IMAGE}
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --jwt wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Wrong jwt model token

Invoke. Pass parameters explicitly
    [Documentation]  Pass parameters explicitly
    ${JWT}=  Refresh security tokens
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}

    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --jwt "${JWT}"
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass parameters through config file
    [Documentation]  Pass parameters through config file
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1 -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Fails with wrong model parameters
    [Documentation]  Fails if model parameters is wrong
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} -p a=1
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Internal Server Error

Invoke. Pass model parameters using json
    [Documentation]  Model parameters as json
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} --json '{"a": 1, "b": 2}'
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass model parameters using json and p
    [Documentation]  Combination json and p model parameters
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} --json '{"a": 1}' -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Specify model endpoint
    [Documentation]  Different model endpoint
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION} --endpoint=feedback -p str=aa -p copies=3
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  aaaaaa
