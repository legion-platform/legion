*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                 Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
Suite Teardown      Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}

*** Test Cases ***
Scale. Nonexistent model service
    [Documentation]  The scale command must fail if a model cannot be found by id
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale this-model-does-not-exsit 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Scale. Nonexistent version of model service
    [Documentation]  The scale command must fail if a model cannot be found by version
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Scale. Scale to zero replicas
    [Documentation]  The scale command must fail if number of replicas is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain       ${res.stderr}  Invalid scale parameter: should be greater then 0

Scale. Scale to negative number of replicas
    [Documentation]  The scale command must fail if number of replicas is negative
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Scale. Zero timeout parameter
    [Documentation]  The scale command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Scale. Negative timeout parameter
    [Documentation]  The scale command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Scale. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_COMMAND_MODEL_ID} 1 --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Scale. Missed the host parameter
    [Documentation]  The scale command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl scale ${TEST_COMMAND_MODEL_ID} 2 --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after resolving of the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Scale. Missed the user parameter
#    [Documentation]  The scale command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_COMMAND_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Scale. Missed the password parameter
#    [Documentation]  The scale command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_COMMAND_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Scale. Wrong token
#    [Documentation]  The scale command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_COMMAND_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect

Inspect. Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl inspect --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Inspect. Missed the user parameter
#    [Documentation]  The inspect command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Inspect. Missed the password parameter
#    [Documentation]  The inspect command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Inspect. Wrong token
#    [Documentation]  The inspect command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect

Undeploy. Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by id
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Undeploy. Nonexistent version of model service
    [Documentation]  The undeploy command must fail if a model cannot be found by version and id
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Undeploy. Nonexistent model service with ignore-not-found parameter
    [Documentation]  The undeploy command must finish successfully if a model does not exists but we there is --ignore-not-found parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Undeploy. Negative grace period parameter
    [Documentation]  The undeploy command must finish successfully when grace period is negative
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --grace-period=-5 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Undeploy. Zero timeout parameter
    [Documentation]  The undeploy command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Undeploy. Negative timeout parameter
    [Documentation]  The undeploy command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Undeploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_5}  ${TEST_COMMAND_MODEL_ID}  ${TEST_MODEL_5_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_COMMAND_MODEL_ID} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Undeploy. Missed the host parameter
    [Documentation]  The undeploy command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl undeploy ${TEST_COMMAND_MODEL_ID} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Undeploy. Missed the user parameter
#    [Documentation]  The undeploy command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_COMMAND_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Undeploy. Missed the password parameter
#    [Documentation]  The undeploy command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_COMMAND_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Undeploy. Wrong token
#    [Documentation]  The undeploy command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_COMMAND_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect

Deploy. Nonexistent image
    [Documentation]  The deploy command must fail if image does not exist
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy nexus-local.cc.epm.kharlamov.biz:443/legion/this-image-does-not:exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Can't get image

Deploy. Negative liveness timeout
    [Documentation]  The deploy command must fail if liveness timeout is negative
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --livenesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy. Negative readiness timeout
    [Documentation]  The deploy command must fail if readiness timeout is negative
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --readinesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy. Zero replicas
    [Documentation]  The deploy command must fail if number of replicas is zero
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --scale 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Deploy. Negative number of replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --scale -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Deploy. Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Deploy. Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Tags]  edi  cli  enclave
    [Setup]  Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_COMMAND_MODEL_ID}
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_5} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Deploy. Missed the host parameter
    [Documentation]  The deploy command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_5} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after resolving of the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Deploy. Missed the user parameter
#    [Documentation]  The deploy command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_5} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Deploy. Missed the password parameter
#    [Documentation]  The deploy command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_5} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Deploy. Wrong token
#    [Documentation]  The deploy command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_5} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect