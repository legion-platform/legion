*** Variables ***
${LOCAL_CONFIG}  legion/config_6_1

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Default Tags        edi  cli  enclave  apps
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                 Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}
Suite Teardown      Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
Test Teardown       Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Refresh security tokens
    [Documentation]  Refresh edi and model tokens. Return model jwt token

    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION}
             Should be equal  ${res.rc}  ${0}
    ${JWT}=  Set variable  ${res.stdout}
    ${res}=  Shell  legionctl config set MODEL_SERVER_URL https://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
             Should be equal  ${res.rc}  ${0}

    [Return]  ${JWT}

*** Test Cases ***
Scale. Nonexistent model service
    [Documentation]  The scale command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose scale this-model-does-not-exsit 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Scale. Nonexistent version of model service
    [Documentation]  The scale command must fail if a model cannot be found by version
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Scale. Scale to zero replicas
    [Documentation]  The scale command must fail if number of replicas is zero
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             should contain       ${res.stderr}  Invalid scale parameter: should be greater then 0

Scale. Scale to negative number of replicas
    [Documentation]  The scale command must fail if number of replicas is negative
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Scale. Zero timeout parameter
    [Documentation]  The scale command must fail if timeout parameter is zero
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Scale. Negative timeout parameter
    [Documentation]  The scale command must fail if it contains negative timeout parameter
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Scale. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

Scale. Missed the host parameter
    [Documentation]  The scale command must fail if it does not contain an edi host
    ${res}=  Shell  legionctl scale ${TEST_COMMAND_MODEL_ID} 2 --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  EDI endpoint is not configured

Undeploy. Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by id
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Undeploy. Nonexistent version of model service
    [Documentation]  The undeploy command must fail if a model cannot be found by version and id
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Undeploy. Nonexistent model service with ignore-not-found parameter
    [Documentation]  The undeploy command must finish successfully if a model does not exists but we there is --ignore-not-found parameter
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

Undeploy. Negative grace period parameter
    [Documentation]  The undeploy command must finish successfully when grace period is negative
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --grace-period=-5 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

Undeploy. Zero timeout parameter
    [Documentation]  The undeploy command must fail if timeout parameter is zero
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Undeploy. Negative timeout parameter
    [Documentation]  The undeploy command must fail if it contains negative timeout parameter
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Undeploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

Deploy. Nonexistent image
    [Documentation]  The deploy command must fail if image does not exist
    ${res}=  Shell  legionctl --verbose deploy nexus-local.cc.epm.kharlamov.biz:443/legion/this-image-does-not:exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Can't get image

Deploy. Negative liveness timeout
    [Documentation]  The deploy command must fail if liveness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --livenesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy. Negative readiness timeout
    [Documentation]  The deploy command must fail if readiness timeout is negative
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --readinesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy. Zero replicas
    [Documentation]  The deploy command must fail if number of replicas is zero
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --scale 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Deploy. Negative number of replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --scale -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Deploy. Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    ${res}=  Shell  legionctl --verbose inspect --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  EDI endpoint is not configured

Wrong token
    [Documentation]  The inspect command must fail if it does not contain a token
    ${res}=  Shell  legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token

             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Without token
    [Documentation]  The inspect command must fail if token is wrong
    ${res}=  Shell  legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}

             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Basic usage
    [Documentation]  Check the login command and inspect command
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose inspect
             Should be equal  ${res.rc}  ${0}

Login. Wrong token
    [Documentation]  The login command must fail if token is wrong
    ${res}=  Shell  legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Override login values
    [Documentation]  Command line parameters must be overrided by config parameters
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Get token from EDI
    [Documentation]  Try to get token from EDI
    ${res} =  Shell  legionctl generate-token --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --token "${DEX_TOKEN}"
              Should be equal       ${res.rc}  ${0}
              Should not be empty   ${res.stdout}

    ${res} =  Shell  legionctl generate-token --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --token "${DEX_TOKEN}"
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Requested field model_version is not set

    ${res} =  Shell  legionctl generate-token --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-version ${TEST_MODEL_5_VERSION} --token "${DEX_TOKEN}"
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Requested field model_id is not set

    ${res} =  Shell  legionctl generate-token --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-version ${TEST_MODEL_5_VERSION} --token wrong-token
              Should not be equal   ${res.rc}  ${0}
              Should contain        ${res.stderr}  Credentials are not correct

Get token from EDI with expiration date set
    [Documentation]  Try to get token from EDI and set it`s expiration date
    ${expiration_date} =    Get future time           ${10}  %Y-%m-%dT%H:%M:%S
    Log  ${expiration_date}
    ${res} =                Shell                     legionctl generate-token --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --expiration-date ${expiration_date} --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --token "${DEX_TOKEN}"
                            Should be equal           ${res.rc}  ${0}
                            Log  ${res.stdout}
    ${token} =              Set variable              ${res.stdout}
    &{res} =                Get component auth page   ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_COMMAND_MODEL_ID}/${TEST_MODEL_5_VERSION}/info  ${EMPTY}  ${token}
                            Dictionary Should Contain Item    ${res}    response_code    200
    ${auth_page} =          Get From Dictionary       ${res}    response_text
                            Should not contain        ${auth_page}    401 Authorization Required

    Ensure component auth page requires authorization   ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}/api/model/${TEST_COMMAND_MODEL_ID}/${TEST_MODEL_5_VERSION}/info  ${token}  ${2}  ${6}

Deploy fails when memory resource is incorect
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_COMMAND_MODEL_ID}
    [Documentation]  Deploy fails when memory resource is incorect
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --memory wrong --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Malformed mem resource

Deploy fails when cpu resource is incorect
    [Setup]         Run EDI undeploy model without version and check    ${MODEL_TEST_ENCLAVE}   ${TEST_COMMAND_MODEL_ID}
    [Documentation]  Deploy fails when cpu resource is incorect
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --cpu wrong --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Malformed cpu resource

Invoke. Empty model service url
    [Documentation]  Fails if model service url is empty
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1 -p b=2 --jwt "some_token"
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  specify model server url

Invoke. Empty jwt
    [Documentation]  Fails if jwt is empty
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}

    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  specify model jwt

Invoke. Wrong jwt
    [Documentation]  Fails if jwt is wrong
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --jwt wrong
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Wrong jwt model token

Invoke. Pass parameters explicitly
    [Documentation]  Pass parameters explicitly
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    ${JWT}=  Refresh security tokens
    # Ensure that next command will not use the config file
    Remove File  ${LOCAL_CONFIG}

    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1 -p b=2 --model-server-url ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --jwt "${JWT}"
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass parameters through config file
    [Documentation]  Pass parameters through config file
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1 -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Fails with wrong model parameters
    [Documentation]  Fails if model parameters is wrong
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} -p a=1
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Internal Server Error

Invoke. Pass model parameters using json
    [Documentation]  Model parameters as json
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --json '{"a": 1, "b": 2}'
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Pass model parameters using json and p
    [Documentation]  Combination json and p model parameters
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --json '{"a": 1}' -p b=2
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  42

Invoke. Specify model endpoint
    [Documentation]  Different model endpoint
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    Refresh security tokens
    ${res}=  Shell  legionctl --verbose invoke --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --endpoint=feedback -p str=aa -p copies=3
             Should be equal  ${res.rc}  ${0}
             Should contain   ${res.stdout}  aaaaaa
