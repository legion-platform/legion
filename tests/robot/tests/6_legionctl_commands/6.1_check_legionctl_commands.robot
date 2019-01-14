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
...                 Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
Suite Teardown      Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
*** Variables ***
${LOCAL_CONFIG}  legion/config
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
             Should contain       ${res.stderr}  Failed to connect

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
             Should contain       ${res.stderr}  Failed to connect

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
    [Teardown]  Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  LEGION_CONFIG=${LOCAL_CONFIG} legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  LEGION_CONFIG=${LOCAL_CONFIG} legionctl --verbose inspect
             Should be equal  ${res.rc}  ${0}

Login. Wrong token
    [Documentation]  The login command must fail if token is wrong
    [Teardown]  Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  LEGION_CONFIG=${LOCAL_CONFIG} legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Override login values
    [Documentation]  Command line parameters must be overrided by config parameters
    [Teardown]  Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  LEGION_CONFIG=${LOCAL_CONFIG} legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  LEGION_CONFIG=${LOCAL_CONFIG} legionctl --verbose inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Get token from EDI
    [Documentation]  Try to get token from EDI
    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --token ${DEX_TOKEN}
              Should be equal  ${res.rc}  ${0}
              Should not be empty   ${res.stdout}

    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --model-version '99.1' --token ${DEX_TOKEN}
              Should not be equal  ${res.rc}  ${0}

    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --token ${DEX_TOKEN}
              Should not be equal  ${res.rc}  ${0}

    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id invalid-model-name --model-version ${TEST_MODEL_5_VERSION} --token ${DEX_TOKEN}
              Should not be equal  ${res.rc}  ${0}

    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-version ${TEST_MODEL_5_VERSION} --token ${DEX_TOKEN}
              Should not be equal  ${res.rc}  ${0}

    ${res} =  Shell  legionctl generate-token ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --model-id ${TEST_COMMAND_MODEL_ID} --model-version ${TEST_MODEL_5_VERSION} --token 'invalid-token'
              Should not be equal  ${res.rc}  ${0}

