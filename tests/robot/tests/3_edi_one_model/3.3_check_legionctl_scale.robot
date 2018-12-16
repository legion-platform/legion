*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Run keywords  Choose cluster context  ${CLUSTER_NAME}  AND
...                 Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
Suite Teardown      Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}

*** Test Cases ***
Nonexistent model service
    [Documentation]  The scale command must fail if a model cannot be found by id
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale this-model-does-not-exsit 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Nonexistent version of model service
    [Documentation]  The scale command must fail if a model cannot be found by version
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} 1 --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Scale to zero replicas
    [Documentation]  The scale command must fail if number of replicas is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain       ${res.stderr}  Invalid scale parameter: should be greater then 0

Scale to negative number of replicas
    [Documentation]  The scale command must fail if number of replicas is negative
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Zero timeout parameter
    [Documentation]  The scale command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} 1 --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout parameter
    [Documentation]  The scale command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} 1 --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose scale ${TEST_EDI_MODEL_ID} 1 --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The scale command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl scale ${TEST_EDI_MODEL_ID} 2 --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after resolving of the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the user parameter
#    [Documentation]  The scale command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_EDI_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the password parameter
#    [Documentation]  The scale command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_EDI_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Wrong token
#    [Documentation]  The scale command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl scale ${TEST_EDI_MODEL_ID} 1 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
