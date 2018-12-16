*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Choose cluster context  ${CLUSTER_NAME}

*** Test Cases ***
Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by id
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Nonexistent version of model service
    [Documentation]  The undeploy command must fail if a model cannot be found by version and id
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_EDI_MODEL_ID} --model-version this-version-does-not-exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  No one model can be found

Nonexistent model service with ignore-not-found parameter
    [Documentation]  The undeploy command must finish successfully if a model does not exists but we there is --ignore-not-found parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy this-model-does-not-exsit --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Negative grace period parameter
    [Documentation]  The undeploy command must finish successfully when grace period is negative
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_EDI_MODEL_ID} --grace-period=-5 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Zero timeout parameter
    [Documentation]  The undeploy command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_EDI_MODEL_ID} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout parameter
    [Documentation]  The undeploy command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_EDI_MODEL_ID} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Setup]  Run EDI deploy and check model started  ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_IMAGE_3}  ${TEST_EDI_MODEL_ID}  ${TEST_MODEL_3_VERSION}
    [Teardown]  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose undeploy ${TEST_EDI_MODEL_ID} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The undeploy command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl undeploy ${TEST_EDI_MODEL_ID} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the user parameter
#    [Documentation]  The undeploy command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_EDI_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the password parameter
#    [Documentation]  The undeploy command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_EDI_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Wrong token
#    [Documentation]  The undeploy command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl undeploy ${TEST_EDI_MODEL_ID} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
